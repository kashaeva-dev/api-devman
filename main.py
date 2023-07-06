from contextlib import suppress

import requests
from environs import Env


def check_api_devman(token):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {token}',
    }
    response = requests.get(url, headers=headers, timeout=5)
    response.raise_for_status()
    print(response.text)


def main():
    env = Env()
    env.read_env()
    devman_token = env.str('DEVMAN_TOKEN')
    while True:
        with suppress(requests.exceptions.ReadTimeout):
            check_api_devman(devman_token)


if __name__ == "__main__":
    main()
