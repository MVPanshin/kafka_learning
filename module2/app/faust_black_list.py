import os
import faust
from models.black_list_message import BlackListMessage
import datetime, random, time
import argparse
import sys
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-0:9092")

# Конфигурация Faust-приложения
app = faust.App(
    "black_list_app",
    broker=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer="json"
)

# Топик стоплистов
blocked_users_topic = app.topic("blocked_users", key_type=str, value_type=BlackListMessage)

@app.agent(blocked_users_topic)
async def send_message(stream):
    # args = parse_custom_args()

    # Создаем сообщение на основе переданных аргументов
    try:
        message = BlackListMessage(
            user_id="user_1",
            target_user_id="user_2",
            is_lock=False
        )
        
        # Отправляем сообщение в топик
        await blocked_users_topic.send(key=message.user_id, value=message)
        logging.info(f"{message.user_id} {'add to ' if message.is_lock else 'remove from '} black list")

    except:
        logging.error(f"Ошибка отправки пользователя в блок")

    # Завершаем работу приложения
    await app.stop()

if __name__ == '__main__':
    app.main()