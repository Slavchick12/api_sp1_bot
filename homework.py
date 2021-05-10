import os
import time
import logging

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
HEADERS = {"Authorization": f"OAuth {PRAKTIKUM_TOKEN}"}
PRAKTIKUM_API = (
    "https://praktikum.yandex.ru/api/user_api/homework_statuses/"
)
VERDICTS = {
    'reviewing': 'Работа взята в ревью.',
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.',
}
CHECKED_WORK = 'У вас проверили работу "{name}"!\n\n{verdict}'
CONNECTION_ERROR = 'Не удалось получить статус: {response}'
SERVER_ERROR = 'Отказ сервера {value}: {response}'


def parse_homework_status(homework):
    name = homework['homework_name']
    status = homework['status']
    if status not in VERDICTS:
        raise ValueError(f'Неожиданный статус {status}')
    verdict = VERDICTS[status]
    return CHECKED_WORK.format(verdict=verdict, name=name)


class ServerError(Exception):
    pass


def get_homework_statuses(current_timestamp):
    data = {"from_date": current_timestamp}
    try:
        response = requests.get(
            PRAKTIKUM_API,
            params=data,
            headers=HEADERS
        )
    except ConnectionError:
        raise ConnectionError(
            CONNECTION_ERROR.format(response=response.text)
        )
    json_response = response.json()
    error_keys = ['error', 'code']
    for key in error_keys:
        if key in json_response:
            raise ServerError(
                SERVER_ERROR.format(
                    value=json_response[key],
                    response=response.text
                )
            )
    return json_response


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    # проинициализировать бота здесь
    logging.debug('Момент запуска бота')
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                bot_client.send_message(
                    parse_homework_status(new_homework.get('homeworks')[0])
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут
        except Exception as error:
            logging.error(f'Бот столкнулся с ошибкой: {error}', exc_info=True)
            time.sleep(20)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '_program.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    main()
