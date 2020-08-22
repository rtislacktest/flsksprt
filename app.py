#!flask/bin/python
from flask import Flask, request, make_response
import requests
import os
import datetime
import json

app = Flask(__name__)

url_post_message     = 'https://slack.com/api/chat.postMessage'
slack_api_dialog_url = 'https://slack.com/api/dialog.open'

bot_rti_token      = os.environ['BOT_RTI_TOKEN']
verification_token = os.environ['VERIFICATION_TOKEN']

def post_to_slack(url_to_post, **kwargs):
    data_info = {'token': bot_rti_token}
    data_info.update(kwargs)
    return requests.post(url_to_post, data_info).json()

def post_message_to_slack(channel, text, blocks=None):
    return requests.post('https://slack.com/api/chat.postMessage', {
        'token': bot_rti_token,
        'channel': channel,
        'text': text,
        'blocks': json.dumps(blocks) if blocks else None
    }).json()

@app.route('/')
def index():
    return 'Hello world'

@app.route('/slack/slash/test', methods=['POST'])
def slash_test():
    token = request.form.get('token')
    if token != verification_token:
        return ''
    text = request.form.get('text')
    return f"Вы успешно выполнили тестовую команду с параметром {text}"

@app.route('/slack/interactive', methods=['POST'])
def interactive():
    slack_req = json.loads(request.values['payload'])
    token = slack_req['token']
    if token != verification_token:
        return ''
    print('*******************')
    print(slack_req)
    print('*******************')
    try:
        if slack_req['type'] == 'shortcut':
            callback_id = slack_req['callback_id']
            return make_response("test", 200)
            #r = requests.post('https://slack.com/api/chat.postMessage',
            #                  f'Вы выбрали shortcut с callback_id={callback_id}').json()
        elif slack_req['type'] == 'message_action':
            callback_id = slack_req['callback_id']
            channel = slack_req['channel']['id']
            message_ts = slack_req['ts']
            msg_text = slack_req['message']['text']
            if callback_id == 'reverse_text':
                post_to_slack(url_post_message,
                              thread_ts = message_ts,
                              text      = msg_text[::-1],
                              channel   = channel)
        elif slack_req['type'] == 'dialog_submission':
            if slack_req['callback_id'] == 'bcalc_id':
                channel = slack_req['channel']['id']
                xlength = int(slack_req['submission']['xlength'])
                xwidth = int(slack_req['submission']['xwidth'])
                xheight = int(slack_req['submission']['xheight'])
                xcount = int(slack_req['submission']['xcount'])
                xprice = int(slack_req['submission']['xprice'])
                bcalc_result = round((xlength * xwidth * xheight / 1000000) * xcount, 2)
                bcalc_price = round(bcalc_result * xprice, 2)
                data_info = {
                    'token': bot_rti_token,
                    'channel': channel,
                    'text': f'для заказа {xcount} досок {xlength}см x {xwidth}см x {xheight}см по цене {xprice}р. за кубометр необходимо заказывать {bcalc_result} кубометров, денег надо {bcalc_price}р.'
                }
                r = requests.post('https://slack.com/api/chat.postMessage', data_info).json()
    except Exception as ex:
        response_text = 'Error: {0}'.format(ex)

    return make_response("", 200)

@app.route('/slack/slash/bcalc', methods=['POST'])
def bcalc():
    token = request.form.get('token')
    if token != verification_token:
        return ''
    channel = request.form.get('channel_name')
    user_id = request.form.get('user_id')
    text = request.form.get('text')
    trigger_id = request.values['trigger_id']

    dialog_bcalc = {
        "callback_id": "bcalc_id",
        "title": "Калькулятор досок",
        "submit_label": "Ok",
        "elements": [
            {
                "type": "text",
                "label": "Длина (см)",
                "name": "xlength",
                "value": "600"
            },
            {
                "type": "text",
                "label": "Ширина (см)",
                "name": "xwidth",
                "value": "20"
            },
            {
                "type": "text",
                "label": "Высота (см)",
                "name": "xheight",
                "value": "4"
            },
            {
                "type": "text",
                "label": "Кол-во досок",
                "name": "xcount",
                "value": "40"
            },
            {
                "type": "text",
                "label": "Цена",
                "name": "xprice",
                "value": "9500"
            }
        ]
    }

    api_data = {
        "token": bot_rti_token,
        "trigger_id": trigger_id,
        "dialog": json.dumps(dialog_bcalc)  # json.dumps(json.loads(dialog_bcalc))
    }
    res = requests.post(slack_api_dialog_url, data=api_data)
    print('res dialog open = ' + res)

    return "Открываю калькулятор досок"

if __name__ == '__main__':
    app.run()
