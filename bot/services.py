from watson_developer_cloud import ConversationV1, NaturalLanguageUnderstandingV1
import watson_developer_cloud.natural_language_understanding.features.v1 \
    as Features
from django.conf import settings


class WatsonService(object):
    """docstring for WatsonService"""
    conversation = None
    nlu = None

    def __init__(self):
        self.conversation = ConversationV1(username=settings.WATSON_USERNAME,
                                           password=settings.WATSON_PASSWORD,
                                           version='2017-04-21')
        self.nlu = NaturalLanguageUnderstandingV1(
            username=settings.NLU_USERNAME,
            password=settings.NLU_PASSWORD,
            version="2017-02-27")

    def send_message(self, message, context={}):
        message_input = {'text': message}
        response = self.conversation.message(workspace_id=settings.WATSON_WORKSPACE,
                                             message_input=message_input,
                                             context=context)
        response_message, buttons, sentiments = self.get_response_message(response)
        return response, response_message, buttons, sentiments

    def get_response_message(self, watson_response):
        out_message = ''
        buttons = None
        detect_sentiment = False
        if watson_response.get('output'):
            output = watson_response.get('output')
            if output.get('text'):
                out_message = ' '.join(output.get('text'))
            if output.get('context'):
                context = output.get('context')
                if context.get('facebook'):
                    facebook_context = context.get('facebook')
                    buttons = facebook_context.get('actions')
                elif context.get('watson'):
                    watson_context = context.get('watson')
                    action = watson_context.get('action')
                    detect_sentiment = action == 'nlu'
        return out_message, buttons, detect_sentiment

    def get_sentiment(self, message):
        response = self.nlu.analyze(
            text=message,
            features=[
                Features.Entities(
                    sentiment=True,
                ),
                Features.Keywords(
                    sentiment=True,
                ),
                Features.Sentiment(),
                Features.Concepts(),
                Features.Categories(),
            ]
        )

        return response
