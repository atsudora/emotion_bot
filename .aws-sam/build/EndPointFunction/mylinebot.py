import os

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,ImageMessage
)


import boto3

#LINE Developersで設定されているアクセストークンとChannel Secretを取得し、設定
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))

client = boto3.client('rekognition')

def lambda_handler(event, context):
    headers = event["headers"]
    body = event["body"]

    # リクエストヘッダーから署名検証のための値を取得
    signature = headers['x-line-signature']

    # 署名を検証し、問題なければhandleに定義されている関数を呼ぶ
    handler.handle(body, signature)

    return {"statusCode": 200, "body": "OK"}

 #テキストメッセージがきた時
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """ TextMessage handler """
    input_text = event.message.text

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage("写真貼れよ"))

#画像に対する処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_content_message(event):
    #画像をtmpファイルに保存して、チャンク
    message_content = line_bot_api.get_message_content(event.message.id)

    file_path = '/tmp/sent-image.jpg'
    with open(file_path, 'wb') as fd:
        for chunk in message_content.iter_content():
            fd.write(chunk)

    #Rekognitionの処理
    with open(file_path, 'rb') as fd:
        sent_image_binary = fd.read()
        response = client.detect_faces(
            Image={
            'Bytes': sent_image_binary,
            },
            Attributes=['ALL']
        )
    print(response)

    #応答
    if is_happy(response):
        message = "元気じゃん"
    else:
        message = "元気ないじゃん"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text = message)
    )
    #画像ファイル削除
    os.remove(file_path)

#検出した画像がハッピーならTrueを返す
def is_happy(result):
    for detail in result['FaceDetails']:
        if most_confidence_emotion(detail['Emotions']) != 'HAPPY':
            return False
    return True


def most_confidence_emotion(emotions):
    max = 0
    result = ""

    for emo in emotions:
        if max < emo['Confidence']:
            max = emo['Confidence']
            result = emo['Type']

    return result
