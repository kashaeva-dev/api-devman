import time
import os
import logging
import logging.handlers
from pathlib import Path
from textwrap import dedent

import requests
import telegram
from environs import Env

BASE_DIR = Path(__file__).resolve().parent.parent

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d - %(levelname)-8s - %(asctime)s - %(funcName)s - %(name)s - %(message)s'
)


class BotHandler(logging.Handler):

    def emit(self, record):
        bot = telegram.Bot(token=tg_bot_logger_token)
        log_entry = self.format(record)
        bot.send_message(chat_id=tg_chat_id,
                         text=fr'{log_entry}',
                         )


rotating_file_handler = logging.handlers.RotatingFileHandler(f'{BASE_DIR}/botlog.txt',
                                                             mode='w', maxBytes=200, backupCount=2)

logger = logging.getLogger(__name__)
logger.addHandler(rotating_file_handler)
logger.addHandler(BotHandler())


def check_api_devman(token, params):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {token}',
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def check_reviews(devman_token, params, bot, tg_chat_id):
    logger.info('Скрипт запущен!')
    last_timestamp = None
    while True:
        logger.info('Новый цикл')
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
                logger.info(f'Обновлений не было, {str(timestamp_to_request)}')
            else:
                current_review = reviews['new_attempts'][0]
                params = {
                    'timestamp': current_review['timestamp'],
                }
                logger.info(f'Пришло новое обновление, {str(current_review)}')
                new_timestamp = current_review['timestamp']
                if new_timestamp == last_timestamp:
                    continue
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
                last_timestamp = new_timestamp
                logger.info(f'Last timestamp is {last_timestamp}')


if __name__ == "__main__":
    env = Env()
    env.read_env()
    devman_token = env.str('DEVMAN_TOKEN')
    tg_bot_token = env('TG_BOT_TOKEN')
    tg_bot_logger_token = env('TG_BOT_LOGGER_TOKEN')
    tg_chat_id = env('TG_CHAT_ID')
    params = {}
    try:
        a = 0/0
        bot = telegram.Bot(token=tg_bot_token)
        check_reviews(devman_token, params, bot, tg_chat_id)
    except Exception as error:
        logger.exception(error)
