from contextlib import suppress

import requests
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


def main():
    env = Env()
    env.read_env()
    devman_token = env.str('DEVMAN_TOKEN')
    params = {}
    while True:
        with suppress(requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
            response = check_api_devman(devman_token, params)
            print(response)
        if response['status'] == 'timeout':
            timestamp_to_request = response['timestamp_to_request']
            params = {
                'timestamp_to_request': timestamp_to_request,
            }


if __name__ == "__main__":
    main()
