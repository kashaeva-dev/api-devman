import logging
import logging.handlers
import time
from pathlib import Path
from textwrap import dedent

import requests
import telegram
from environs import Env


logger = logging.getLogger(__file__)


class BotHandler(logging.Handler):
    def __init__(self, tg_bot_logger_token, tg_chat_id):
        super().__init__()
        self.tg_bot_logger_token = tg_bot_logger_token
        self.tg_chat_id = tg_chat_id

    def emit(self, record):
        bot = telegram.Bot(token=self.tg_bot_logger_token)
        log_entry = self.format(record)
        bot.send_message(chat_id=self.tg_chat_id,
                         text=fr'{log_entry}',
                         )


def check_api_devman(token, params):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {token}',
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def check_reviews(devman_token, params, bot, tg_chat_id, logger):
    last_timestamp = None
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
                params = {
                    'timestamp': current_review['timestamp'],
                }

                new_timestamp = current_review['timestamp']
                if new_timestamp == last_timestamp:
                    continue
                if current_review['is_negative']:
                    bot.send_message(chat_id=tg_chat_id,
                                     text=dedent(fr"""
                                     Преподаватель проверил работу "<b>{current_review["lesson_title"]}</b>".
                                     К сожалению, в работе нашлись ошибки.
                                     Ссылка на работу: {current_review["lesson_url"]}
                                     """),
                                     parse_mode=telegram.ParseMode.HTML,
                                     )
                else:
                    bot.send_message(chat_id=tg_chat_id,
                                     text=dedent(fr"""
                                     Преподаватель проверил работу "<b>{current_review["lesson_title"]}</b>".
                                     Преподавателю все понравилось, можно приступать к следующему уроку.
                                     """),
                                     parse_mode=telegram.ParseMode.HTML,
                                     )
                last_timestamp = new_timestamp


def config_logger(tg_bot_logger_token, tg_chat_id, logger):
    BASE_DIR = Path(__file__).resolve().parent

    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d - %(levelname)-8s - %(asctime)s - %(funcName)s - %(name)s - %(message)s',
    )

    rotating_file_handler = logging.handlers.RotatingFileHandler(f'{BASE_DIR}/botlog.txt',
                                                                 mode='w', maxBytes=200, backupCount=2)

    logger.addHandler(rotating_file_handler)
    logger.addHandler(BotHandler(tg_bot_logger_token, tg_chat_id))


def main():
    env = Env()
    env.read_env()
    devman_token = env.str('DEVMAN_TOKEN')
    tg_bot_token = env('TG_BOT_TOKEN')
    tg_bot_logger_token = env('TG_BOT_LOGGER_TOKEN')
    tg_chat_id = env('TG_CHAT_ID')
    params = {}

    config_logger(tg_bot_logger_token, tg_chat_id, logger)

    try:
        bot = telegram.Bot(token=tg_bot_token)
        check_reviews(devman_token, params, bot, tg_chat_id, logger)
    except Exception as error:
        logger.exception(error)


if __name__ == "__main__":
    main()
