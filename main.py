import time
from textwrap import dedent

import requests
import telegram
from environs import Env


def check_api_devman(token, params):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {token}',
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def check_reviews(devman_token, params, bot, tg_chat_id):
    while True:
        try:
            reviews = check_api_devman(devman_token, params)
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            time.sleep(30)
        else:
            if reviews['status'] == 'timeout':
                timestamp_to_request = reviews['timestamp_to_request']
                params = {
                    'timestamp': timestamp_to_request,
                }
            else:
                current_review = reviews['new_attempts'][0]
                if current_review['is_negative']:
                    bot.send_message(chat_id=tg_chat_id,
                                     text=dedent(f"""
                                     Преподаватель проверил работу *"{current_review["lesson_title"]}"*\.
                                     К сожалению, в работе нашлись ошибки\.
                                     [Ссылка на работу]({current_review["lesson_url"]})
                                     """),
                                     parse_mode=telegram.ParseMode.MARKDOWN_V2,
                                     )
                else:
                    bot.send_message(chat_id=tg_chat_id,
                                     text=dedent(f"""
                                     Преподаватель проверил работу *"{current_review["lesson_title"]}"*\.
                                     Преподавателю все понравилось, можно приступать к следующему уроку\.
                                     """),
                                     parse_mode=telegram.ParseMode.MARKDOWN_V2,
                                     )


if __name__ == "__main__":
    env = Env()
    env.read_env()
    devman_token = env.str('DEVMAN_TOKEN')
    tg_bot_token = env('TG_BOT_TOKEN')
    tg_chat_id = env('TG_CHAT_ID')
    params = {}
    bot = telegram.Bot(token=tg_bot_token)
    check_reviews(devman_token, params, bot, tg_chat_id)
