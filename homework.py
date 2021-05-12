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
CONNECTION_ERROR = ('{error}: не удалось получить '
                    'статус: {url}, {params}, {headers}')
SERVER_ERROR = 'Отказ сервера {value}: {url}, {params}, {headers}'
UNEXPECTED_STATUS = 'Неожиданный статус {status}'
BOT_START = 'Момент запуска бота'
BOT_ERROR = 'Бот столкнулся с ошибкой: {error}'


def parse_homework_status(homework):
    status = homework['status']
    if status not in VERDICTS:
        raise ValueError(UNEXPECTED_STATUS.format(status=status))
    return CHECKED_WORK.format(
        verdict=VERDICTS[status],
        name=homework['homework_name']
    )


class ServerError(Exception):
    pass


def get_homework_statuses(current_timestamp):
    data = {"from_date": current_timestamp}
    request_details = dict(url=PRAKTIKUM_API, params=data, headers=HEADERS)
    try:
        response = requests.get(**request_details)
        logging.debug(response.json().get("homeworks"))
    except requests.RequestException as error:
        raise ConnectionError(
            CONNECTION_ERROR.format(error=error, **request_details)
        )
    json_response = response.json()
    for key in ['error', 'code']:
        if key in json_response:
            raise ServerError(
                SERVER_ERROR.format(
                    value=json_response[key],
                    **request_details
                )
            )
    return json_response


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    # проинициализировать бота здесь
    logging.debug(BOT_START)
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут
        except Exception as error:
            logging.error(BOT_ERROR.format(error=error), exc_info=True)
            time.sleep(20)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
    )
    main()
