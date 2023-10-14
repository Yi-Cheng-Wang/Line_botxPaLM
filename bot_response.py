from django.shortcuts import render

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import *
from . import models

import requests
import json

# Channel access token
line_bot_api = LineBotApi('__YOUR_LINE_BOT_API__')
# Channel secret
parser = WebhookParser('__YOUR_PARSER__')

# PaLM
API_KEY = '__YOUR_API_KEY__'

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()

        for event in events:
            uid = event.source.user_id
            profile = line_bot_api.get_profile(uid)
            name = profile.display_name
            message = []
            output = curl_request(event.message.text)
            output = json.loads(output)
            message = add_message(message, output['candidates'][0]['output'])
            line_bot_api.reply_message(event.reply_token, message)
        return HttpResponse()
    else:
        return HttpResponseBadRequest()

def add_message(message, to_add):
    message.append(TextSendMessage(text=to_add))
    return message

def add_image(message, url):
    message.append(ImageSendMessage(original_content_url=url, preview_image_url=url))
    return message

def add_sticker(message, p_id, s_id):
    #You can find package_id & sticker_id at https://developers.line.biz/en/docs/messaging-api/sticker-list/
    message.append(StickerSendMessage(package_id=p_id, sticker_id=s_id))
    return message

def curl_request(keyword):
    url = 'https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateText?key={}'.format(API_KEY)
    headers = {'Content-Type': 'application/json'}
    data = {
        'prompt': {
            'text': f"__YOUR_PROMPT__",
            'temperature': 0.7,
            'top_k': 40,
            'top_p': 0.95,
            'candidate_count': 1,
            'max_output_tokens': 1024,
            'stop_sequences': [],
            'safety_settings': [
                {'category': 'HARM_CATEGORY_DEROGATORY', 'threshold': 1},
                {'category': 'HARM_CATEGORY_TOXICITY', 'threshold': 1},
                {'category': 'HARM_CATEGORY_VIOLENCE', 'threshold': 2},
                {'category': 'HARM_CATEGORY_SEXUAL', 'threshold': 2},
                {'category': 'HARM_CATEGORY_MEDICAL', 'threshold': 2},
                {'category': 'HARM_CATEGORY_DANGEROUS', 'threshold': 2}
            ]
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    output = response.text
    return output