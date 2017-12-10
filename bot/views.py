# -*- coding: utf-8 -*-
from bot.models import Incident, IncidentType
from bot.serializers import IncidentSerializer
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import list_route
from django.http import HttpResponse
from rest_framework import status
from django.conf import settings
from django.db.models import Count
import json
import requests


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

    # @list_route(methods=['get'])
    # def type_genre(self, request):
    #     conversations = Conversation.objects.all().values(
    #         'genre', 'violence_type').order_by().annotate(entries=Count('genre'))
    #     genres = {"Masculino": {}, "Femenino": {}}
    #     violence_types = []
    #     for conversation_group in conversations:
    #         if conversation_group['genre'] is not None:
    #             genres[conversation_group['genre']][
    #                 conversation_group['violence_type']] = conversation_group['entries']
    #             if conversation_group['violence_type'] not in violence_types:
    #                 violence_types.append(conversation_group['violence_type'])

    #     response = {
    #         "entries": genres,
    #         "violence_type": violence_types,
    #     }
    #     return Response(response)

    # @list_route(methods=['get'])
    # def section_emotion(self, request):
    #     conversations = Conversation.objects.all().values(
    #         'grade', 'grade_section', 'grade_level', 'sentiment').order_by().annotate(entries=Count('sentiment'))
    #     classrooms = {}
    #     for conversation_group in conversations:
    #         section_identifier = conversation_group[
    #             'grade'] + '-' + conversation_group['grade_section'].upper()
    #         if conversation_group['sentiment'] is not None:
    #             if section_identifier not in classrooms:
    #                 classrooms[section_identifier] = {}
    #             classrooms[section_identifier][conversation_group[
    #                 'sentiment']] = conversation_group['entries']

    #         response = {
    #             "entries": classrooms,
    #             "classrooms": ['negative', 'neutral', 'positive'],
    #         }

    #     return Response(response)

    @list_route(methods=['post', 'get'])
    def webhook(self, request):
        if request.method == 'POST':
            print(request.data)
            sender_id, message, button = self.recive_message(data=request.data)
            if sender_id and message:
                self.make_response(sender_id, message, button)
            return Response(status=status.HTTP_201_CREATED)
        return HttpResponse(request.GET['hub.challenge'], content_type='text/plain')

    def make_response(self, sender_id, message, button):
        conversation, created = Incident.objects.get_or_create(sender_id=sender_id, ended=None)
        if button is None:
            button = {}
        if created:
            button = {
                'quick_replies': self.initial_converstation('START'),
            }
            self.send_message(sender_id, str('¡Hola! ¿Qué deseas realizar?'), **button)
        else:

            response = self.get_response(conversation, message)
            new_button = self.get_new_buttons(conversation, message)
            if new_button is not None:
                button = new_button
            self.send_message(sender_id, str(response), **button)

    def get_new_buttons(self, conversation, message):
        if conversation.request_kind:
            return self.get_kind_replys()
        elif conversation.proof_requested:
            return self.get_proof_replys()
        elif conversation.location_requested:
            return self.get_location_replys()
        return None

    def get_location_replys(self):
        return {
            'quick_replies': [
                {
                    'content_type': 'location'
                }
            ]
        }

    def get_proof_replys(self):
        return {
            'quick_replies': [
                {
                    'content_type': 'text',
                    'title': 'Si',
                    'payload': 'have_proof',
                },
                {
                    'content_type': 'text',
                    'title': 'No',
                    'payload': 'no_proof',
                },
            ]
        }

    def get_kind_replys(self):
        return { 'quick_replies':
            [
                {
                    'content_type': 'text',
                    'title': 'Hurto',
                    'payload': 'HURTO',
                },
                {
                    'content_type': 'text',
                    'title': 'Robo',
                    'payload': 'ROBO',
                },
                {
                    'content_type': 'text',
                    'title': 'Acoso sexual o Violación',
                    'payload': 'ACOSO-VIOLACION',
                },
                {
                    'content_type': 'text',
                    'title': 'Comercialización de drogas',
                    'payload': 'DROGAS',
                },
                {
                    'content_type': 'text',
                    'title': 'Homicidio',
                    'payload': 'HOMICIDIO',
                },
                {
                    'content_type': 'text',
                    'title': 'Otros',
                    'payload': 'OTROS',
                },
            ]
        }

    def get_response(self, conversation, message):
        if message == 'not_anonymous_incident':
            conversation.started = True
            conversation.is_anonymous = False
            conversation.save()
            return 'Cual es tu DNI?'
        elif message == 'pre-incident':
            conversation.type = IncidentType.objects.get(id=IncidentType.PRE_INCIDENT)
            conversation.save()
            return '¿Deseas que la denuncia sea anónima?'
        elif message == 'incident':
            conversation.type = IncidentType.objects.get(id=IncidentType.INCIDENT)
            conversation.location_requested = True
            conversation.save()
            return 'Por favor envía la ubicación de la zona que consideras peligrosa'
        elif message == 'anonymous_incident':
            conversation.started = True
            conversation.is_anonymous = True
            conversation.save()

        if conversation.type.id == IncidentType.INCIDENT:
            if conversation.latitude is None and conversation.longitude is None and conversation.location_requested is None:
                conversation.location_requested = True
                conversation.save()
                return 'Por favor envía la ubicación donde sucedieron los hechos'

            elif conversation.description is None and conversation.latitude is None and conversation.longitude is None:
                coordinates = message.split(',')
                conversation.latitude = coordinates[0]
                conversation.longitude = coordinates[1]
                conversation.location_requested = False
                conversation.save()
                return 'Por favor describe las características de  la zona reportada (e.g. establecimientos cercanos, semáforos, cruces, etc.)'
            elif conversation.kind is None and conversation.description is None:
                conversation.description = message
                conversation.request_kind = True
                conversation.save()
                return '¿Cuál de las siguientes opciones describe lo que sucedido?'
            elif conversation.date is None and conversation.kind is None:
                conversation.kind = message
                conversation.request_kind = False
                conversation.save()
                return '¿Qué día fue la última vez ocurrió algo en la zona?'
            if conversation.have_proof is None and conversation.proof_requested is None and conversation.date is None:
                conversation.date = message
                conversation.proof_requested = True
                conversation.save()
                return '¿Tienes pruebas de lo ocurrido?'

            if message == 'have_proof':
                conversation.proof_requested = False
                conversation.have_proof = True
                conversation.save()
            elif message == 'no_proof':
                conversation.proof_requested = False
                conversation.have_proof = False
                conversation.save()

            if conversation.have_proof and conversation.evidence_media is None and conversation.evidence_requested is None:
                conversation.evidence_requested = True
                conversation.save()
                return 'Adjunta tus pruebas a continuación:'

            if conversation.evidence_media is None and conversation.evidence_requested:
                conversation.evidence_media = message
                conversation.ended = True
                conversation.save()
                return '¡Muchas gracias por tu aporte! El código de tu registro es {0}. Puedes hacerle seguimiento en: www.policibot.pe. Recuerda también que comisaría más cercana es (NOMBRE COMISARIA), ubicada en (DIRECCIÓN).'.format(conversation.id)


        if not conversation.is_anonymous:
            if conversation.genre is None and conversation.name is None:
                conversation.name = message
                conversation.save()
                return '¿Eres hombre o mujer?'
            elif conversation.age is None and conversation.genre is None:
                conversation.genre = message
                conversation.save()
                return '¿Cuántos años tienes?'
            elif conversation.civil_state is None and conversation.age is None:
                conversation.age = int(message)
                conversation.save()
                return '¿Cuál es tu estado civil?'
            elif conversation.profession is None and conversation.civil_state is None:
                conversation.civil_state = message
                conversation.save()
                return '¿Cuál es tu profesión?'
            elif conversation.address is None and conversation.profession is None:
                conversation.profession = message
                conversation.save()
                return '¿Cuál es la dirección de tu domicilio?'
            elif conversation.address is None and conversation.profession is not None:
                conversation.address = message
                conversation.save()

        if conversation.date is None and conversation.requested_date is None:
            conversation.requested_date = True
            conversation.save()
            return '¿Qué día paso?'
        elif conversation.time is None and conversation.date is None:
            conversation.date = message
            conversation.save()
            return '¿A qué hora paso?'
        elif conversation.kind is None and conversation.time is None:
            conversation.time = message
            conversation.request_kind = True
            conversation.save()
            return '¿Cuál de las siguientes opciones describe lo que sucedido?'
        elif conversation.description is None and conversation.kind is None:
            conversation.kind = message
            conversation.request_kind = False
            conversation.save()
            return 'Describe lo sucedido utilizando los detalles que consideres necesarios.'
        elif conversation.description is None and conversation.kind is not None:
            conversation.description = message
            conversation.save()

        if conversation.have_proof is None and conversation.proof_requested is None:
            conversation.proof_requested = True
            conversation.save()
            return '¿Tienes pruebas de lo ocurrido?'

        if message == 'have_proof':
            conversation.proof_requested = False
            conversation.have_proof = True
            conversation.save()
        elif message == 'no_proof':
            conversation.proof_requested = False
            conversation.have_proof = False
            conversation.save()

        if conversation.have_proof and conversation.evidence_media is None and conversation.evidence_requested is None:
            conversation.evidence_requested = True
            conversation.save()
            return 'Adjunta tus pruebas a continuación:'

        if conversation.evidence_media is None and conversation.evidence_requested:
            conversation.evidence_media = message
            conversation.save()

        if conversation.latitude is None and conversation.longitude is None and conversation.location_requested is None:
            conversation.location_requested = True
            conversation.save()
            return 'Por favor envía la ubicación donde sucedieron los hechos'

        if conversation.location_requested:
            print(message)
            coordinates = message.split(',')
            conversation.latitude = coordinates[0]
            conversation.longitude = coordinates[1]
            conversation.ended = True
            conversation.location_requested = False
            conversation.save()
            if conversation.is_anonymous:
                return '¡Muchas gracias por tu aporte! El código de tu caso es {0}. Puedes hacerle seguimiento en: www.policibot.pe'.format(conversation.id)
            return '¡Muchas gracias por tu aporte! El código de tu caso es {0}. Acércate a la comisaria de (NOMBRE COMISARIA), ubicada en (DIRECCIÓN) para continuar con tu denuncia.'.format(conversation.id)

        return 'Default get message'


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
                        if messaging_event.get('message').get('text') and messaging_event.get('message').get('quick_reply') is None:
                            message_text = messaging_event["message"]["text"]
                            return sender_id, message_text, None
                        elif messaging_event.get('message').get('attachments'):
                            message = messaging_event.get('message').get('attachments')[0].get('payload').get('url')
                            if not message:
                                coordinates = messaging_event.get('message').get('attachments')[0].get('payload').get('coordinates')
                                message = '{0},{1}'.format(coordinates['lat'], coordinates['long'])
                            return sender_id, message, None
                        elif messaging_event.get('message').get('quick_reply'):
                            message, buttons = self.handle_quick_reply(messaging_event.get('message').get('quick_reply'))
                            return sender_id, message, buttons

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

    def send_message(self, recipient_id, message_text, buttons=None, quick_replies=None):

        self.log("sending message to {recipient}: {text}".format(
            recipient=recipient_id, text=message_text))

        params = {
            "access_token": settings.BOT_APP_TOKEN
        }
        headers = {
            "Content-Type": "application/json"
        }
        if buttons is None and quick_replies is None:
            message = {'text': message_text}
        elif quick_replies is not None:
            message = {
                'text': message_text,
                'quick_replies': [self.map_quick_reply(quick_reply) for quick_reply in quick_replies]
            }
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

    def map_quick_reply(self, quick_reply):
        return {
            'content_type': quick_reply.get('content_type', 'text'),
            'title': quick_reply.get('title', 'title'),
            'payload': quick_reply.get('payload', 'default_quick_reply')
        }

    def handle_quick_reply(self, quick_reply):
        payload = quick_reply.get('payload')
        if payload == 'pre-incident':
            buttons = {
                'quick_replies': self.initial_converstation('pre-incident')
            }
            return payload, buttons
        elif payload == 'not_anonymous_incident':
            return payload, None
        else:
            return payload, None
        return 'Default Message', None


    def initial_converstation(self, payload):
        if payload == 'pre-incident':
            return [
                {
                    'content_type': 'text',
                    'title': 'Si',
                    'payload': 'anonymous_incident',
                },
                {
                    'content_type': 'text',
                    'title': 'No',
                    'payload': 'not_anonymous_incident',
                }
            ]
        if payload == 'START':
            return [
                {
                    'content_type': 'text',
                    'title': 'Pre-Denuncia',
                    'payload': 'pre-incident',
                },
                {
                    'content_type': 'text',
                    'title': 'Reportar una zona peligrosa',
                    'payload': 'incident',
                }
            ]
