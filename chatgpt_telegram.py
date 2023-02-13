import requests
import json
import os
import threading
from random import randrange
from properties import *

TOPICS = [
    ['Очаровательном', 'придумай комплимент для прекрасной девочки по имени Алина Острикова'],
    ['Дружелюбном', 'придумай мотивационную фразу для творческой девочки по имени Алина'],
    ['Юмористическом', 'придумай добрую шутку'],
    ['Успокаивающем', 'скажи другими словами, что у меня все будет хорошо'],
    ['Очаровательном', 'интересный факт - ты самая замечательная'],
    ['Саркастичном', 'скажи о том, что самовлюбленность это плохо'],
    ['/img', 'котята поздравляют с 14 февраля'],
    ['/img', 'влюбленная пара радуется жизни'],
    ['/img', 'влюбленная пара в Париже']
]
def generateCompliment(chat_id, msg_id):
    topic = TOPICS[randrange(len(TOPICS))]
    tone = topic[0]
    prompt = topic[1]
    if (tone == '/img'):
        bot_response = openAImage(prompt)
        print(telegram_bot_sendimage(bot_response, chat_id, msg_id))
    else:
        BOT_PERSONALITY = f'Ответь в {tone} тоне. '
        bot_response = openAI(f"{BOT_PERSONALITY}{prompt}")
        print(telegram_bot_sendtext(bot_response, chat_id, msg_id))

# Ответ от openAi
def openAI(prompt):
    # делаем запрос на сервер с ключами
    response = requests.post(
        'https://api.openai.com/v1/completions',
        headers={'Authorization': f'Bearer {API_KEY}'},
        json={'model': MODEL, 'prompt': prompt, 'temperature': 0.4, 'max_tokens': 300}
    )

    result = response.json()
    final_result = ''.join(choice['text'] for choice in result['choices'])
    return final_result

# Функция обработки изображений
def openAImage(prompt):
    # запрос на  OpenAI API
    resp = requests.post(
        'https://api.openai.com/v1/images/generations',
        headers={'Authorization': f'Bearer {API_KEY}'},
        json={'prompt': prompt,'n' : 1, 'size': '1024x1024'}
    )
    response_text = json.loads(resp.text)
      
    return response_text['data'][0]['url']

# Функция отправки в заданную телеграм группу
def telegram_bot_sendtext(bot_message,chat_id,msg_id):
    data = {
        'chat_id': chat_id,
        'text': bot_message,
        'reply_to_message_id': msg_id
    }
    response = requests.post(
        'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage',
        json=data
    )
    return response.json()

# Функция, которая отправляет изображение в определенную группу телеграмм 
def telegram_bot_sendimage(image_url, group_id, msg_id):
    data = {
        'chat_id': group_id, 
        'photo': image_url,
        'reply_to_message_id': msg_id
    }
    url = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendPhoto'
    
    response = requests.post(url, data=data)
    return response.json()

# Функция получения последних запросов от пользователей в группе Telegram,
# генерирует ответ, используя OpenAI, и отправляет ответ обратно в группу.

def Chatbot():
    # Retrieve last ID message from text file for ChatGPT update
    cwd = os.getcwd()
    filename = cwd + '/chatgpt.txt'
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("1")
    else:
        print("File Exists")    

    with open(filename) as f:
        last_update = f.read()
        
    # Проверить наличие новых сообщений в группе Telegram
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update}'
    response = requests.get(url)
    data = json.loads(response.content)
        
    for result in data['result']:
        try:
          # Проверить наличие новых сообщений
            if float(result['update_id']) > float(last_update):
                # Checking for new messages that did not come from chatGPT
                if not result['message']['from']['is_bot']:
                    last_update = str(int(result['update_id']))
                    msg_id = str(int(result['message']['message_id']))
                    chat_id = str(result['message']['chat']['id'])

                     # Получение идентификатора сообщения отправителя запроса
                    if '/img' in result['message']['text']:
                        prompt = result['message']['text'].replace("/img", "")
                        bot_response = openAImage(prompt)
                        print(telegram_bot_sendimage(bot_response, chat_id, msg_id))

                    # Проверка того, что пользователь упомянул имя пользователя чат-бота в сообщении или команда /tellme
                    if '/tellme' in result['message']['text'] or BOT_NAME in result['message']['text']:
                        prompt = result['message']['text'].replace(BOT_NAME, "")
                        generateCompliment(chat_id, msg_id)
                    # Проверка того, что пользователь отвечает боту ChatGPT
                    # if 'reply_to_message' in result['message']:
                    #     if result['message']['reply_to_message']['from']['is_bot']:
                    #         prompt = result['message']['text']
                    #         generateCompliment(chat_id, msg_id)
        except Exception as e: 
            print(e)

    with open(filename, 'w') as f:
        f.write(last_update)
    
    return "done"

def main():
    timertime=5
    Chatbot()
   
    threading.Timer(timertime, main).start()

if __name__ == "__main__":
    main()