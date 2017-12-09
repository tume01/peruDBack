# -*- coding: utf-8 -*-
from bot.models import Message, Conversation
from bot.serializers import MessageSerializer
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route
from django.http import HttpResponse
from rest_framework import status
from django.conf import settings
from bot.services import WatsonService
from django.db.models import Count
import json
import requests


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    @list_route(methods=['get'])
    def type_genre(self, request):
        conversations = Conversation.objects.all().values(
            'genre', 'violence_type').order_by().annotate(entries=Count('genre'))
        genres = {"Masculino": {}, "Femenino": {}}
        violence_types = []
        for conversation_group in conversations:
            if conversation_group['genre'] is not None:
                genres[conversation_group['genre']][
                    conversation_group['violence_type']] = conversation_group['entries']
                if conversation_group['violence_type'] not in violence_types:
                    violence_types.append(conversation_group['violence_type'])

        response = {
            "entries": genres,
            "violence_type": violence_types,
        }
        return Response(response)

    @list_route(methods=['get'])
    def section_emotion(self, request):
        conversations = Conversation.objects.all().values(
            'grade', 'grade_section', 'grade_level', 'sentiment').order_by().annotate(entries=Count('sentiment'))
        classrooms = {}
        for conversation_group in conversations:
            section_identifier = conversation_group[
                'grade'] + '-' + conversation_group['grade_section'].upper()
            if conversation_group['sentiment'] is not None:
                if section_identifier not in classrooms:
                    classrooms[section_identifier] = {}
                classrooms[section_identifier][conversation_group[
                    'sentiment']] = conversation_group['entries']

            response = {
                "entries": classrooms,
                "classrooms": ['negative', 'neutral', 'positive'],
            }

        return Response(response)

    @list_route(methods=['post', 'get'])
    def webhook(self, request):
        if request.method == 'POST':
            print(request.data)
            sender_id, message, initial_converstation = self.recive_message(
                data=request.data)
            if sender_id and message:
                self.make_response(sender_id, message, initial_converstation)
            return Response(status=status.HTTP_201_CREATED)
        return HttpResponse(request.GET['hub.challenge'], content_type='text/plain')

    def make_response(self, sender_id, message, initial_converstation):
        context = {}
        conversation, created = Conversation.objects.get_or_create(
            sender_id=sender_id)
        context = conversation.context
        try:
            if conversation.detect_sentiment is not None and conversation.detect_sentiment:
                sentiment_response = WatsonService().get_sentiment(message)
                print('sentiments')
                print(sentiment_response)
                sentiment_analyzis = sentiment_response.get(
                    'sentiment').get('document')
                conversation.sentiment = sentiment_analyzis.get('label')
                conversation.sentiment_value = sentiment_analyzis.get('score')
                conversation.detect_sentiment = False
                if sentiment_analyzis.get('label') == 'negative':
                    message = 'negativo'
                elif sentiment_analyzis.get('label') == 'positive':
                    message = 'positivo'
                else:
                    message = 'normal'
        except Exception as e:
            print(e)

        watson_response, watson_message, buttons, sentiment = WatsonService().send_message(message,
                                                                                           context)
        new_context = watson_response.get('context')
        conversation.context = new_context
        print(conversation.detect_sentiment)
        print("cambio")
        print(sentiment)
        self.update_conversation(conversation, watson_response.get('entities'))
        conversation.detect_sentiment = sentiment
        conversation.save()

        self.send_message(sender_id, str(watson_message), buttons)

    def update_conversation(self, conversation, entities):
        for entity in entities:
            value = entity.get('value')
            if entity.get('entity') == 'nivel':
                conversation.grade_level = value
            elif entity.get('entity') == 'alguien':
                conversation.confidence_person = value
            elif entity.get('entity') == 'grado_primaria':
                conversation.grade = value
            elif entity.get('entity') == 'grado_secundaria':
                conversation.grade = value
            elif entity.get('entity') == 'seccion':
                conversation.grade_section = value
            elif entity.get('entity') == 'forma_violencia':
                conversation.violence_type = value
            elif entity.get('entity') == 'distrito':
                conversation.district = value
            elif entity.get('entity') == 'grado':
                conversation.grade = value
            elif entity.get('entity') == 'ubicacion':
                conversation.problem_location = value
            elif entity.get('entity') == 'genero':
                conversation.genre = value
        return conversation.save()

    def recive_message(self, data={}):
        if data["object"] == "page":

            for entry in data["entry"]:
                for messaging_event in entry["messaging"]:

                    # someone sent us a message
                    if messaging_event.get("message"):

                        # the facebook ID of the person sending you the message
                        sender_id = messaging_event["sender"]["id"]
                        # the recipient's ID, which should be your page's facebook
                        # ID
                        recipient_id = messaging_event["recipient"]["id"]
                        try:
                            message_text = messaging_event["message"][
                                "text"]  # the message's text

                            # reply = predict(message_text)
                            return sender_id, message_text, False
                        except:
                            self.send_message(sender_id, str(
                                "Sorry! I didn't get that."))
                    if messaging_event.get("delivery"):  # delivery confirmation
                        pass

                    if messaging_event.get("optin"):  # optin confirmation
                        pass

                    # user clicked/tapped "postback" button in earlier message
                    if messaging_event.get("postback"):
                        postback = messaging_event.get("postback")
                        sender_id = messaging_event["sender"]["id"]
                        message_text = messaging_event['postback']['title']
                        initial_converstation = postback.get(
                            'payload') == 'START'
                        return sender_id, message_text, initial_converstation

    def send_message(self, recipient_id, message_text, buttons=None):

        self.log("sending message to {recipient}: {text}".format(
            recipient=recipient_id, text=message_text))

        params = {
            "access_token": settings.BOT_APP_TOKEN
        }
        headers = {
            "Content-Type": "application/json"
        }
        if buttons is None:
            message = {'text': message_text}
        else:
            message = {
                'attachment': {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": message_text,
                        "buttons": [self.map_buttons(button) for button in buttons],
                    }
                }
            }
        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "message": message,
        })

        r = requests.post("https://graph.facebook.com/v2.6/me/messages",
                          params=params, headers=headers, data=data)
        if r.status_code != 200:
            self.log(r.status_code)
            self.log(r.text)

    def log(self, message):  # simple wrapper for logging to stdout on heroku
        print(str(message))

    def map_buttons(self, button_text):
        return {
            "type": "postback",
            "title": button_text,
            "payload": button_text,
        }
