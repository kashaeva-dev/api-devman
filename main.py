from contextlib import suppress

import requests
import telegram
from environs import Env


def check_api_devman(token, params):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {token}',
    }
    if params:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
    else:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    return response.json()


def check_reviews(devman_token, params, bot, tg_chat_id):
    while True:
        with suppress(requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            response = check_api_devman(devman_token, params)
        if response['status'] == 'timeout':
            timestamp_to_request = response['timestamp_to_request']
            params = {
                'timestamp_to_request': timestamp_to_request,
            }
        else:
            review = response['new_attempts'][0]
            if review['is_negative']:
                bot.send_message(chat_id=tg_chat_id,
                                 text=f'Преподаватель проверил работу *"{review["lesson_title"]}"*\.\n\n'
                                      'К сожалению, в работе нашлись ошибки\.\n'
                                      f'[Ссылка на работу]({review["lesson_url"]})',
                                 parse_mode=telegram.ParseMode.MARKDOWN_V2,
                                 )
            else:
                bot.send_message(chat_id=tg_chat_id,
                                 text=f'Преподаватель проверил работу *"{review["lesson_title"]}"*\.\n\n'
                                      'Преподавателю все понравилось, можно приступать к следующему уроку\!',
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
