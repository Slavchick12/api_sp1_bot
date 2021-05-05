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


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status == 'reviewing':
        verdict = 'Работа взята в ревью.'
    elif homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework_status == 'approved':
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    data = {"from_date": current_timestamp}
    headers = {"Authorization": f"OAuth {PRAKTIKUM_TOKEN}"}
    homework_statuses = requests.get(
        "https://praktikum.yandex.ru/api/user_api/homework_statuses/",
        params=data,
        headers=headers
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info('Отправка сообщений')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    # проинициализировать бота здесь
    logging.debug('Момент запуска бота')
    current_timestamp = int(time.time())  # начальное значение timestamp

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0])
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )  # обновить timestamp
            time.sleep(300)  # опрашивать раз в пять минут

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            logging.error(f'Бот столкнулся с ошибкой: {e}')
            bot_client.send_message(
                chat_id=CHAT_ID,
                text=f'Бот столкнулся с ошибкой: {e}'
            )
            time.sleep(5)


if __name__ == '__main__':
    main()
