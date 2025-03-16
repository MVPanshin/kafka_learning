import os
import faust
from models.message import Message
from models.black_list_message import BlackListMessage
from constants.constants import chat_messages
import datetime, random, time

import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Чтение переменной окружения
USER_ID = int(os.getenv("USER_ID", "user_1"))
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-0:9092")

# Конфигурация Faust-приложения
app = faust.App(
    "messages_app",
    broker=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer="json"
)

# Топик, куда генерим сообщения для данных
messages_topic = app.topic("messages", key_type=str, value_type=Message)

# генерим идентификатор другого пользователя
def generate_user_id():
    return 'user_' + str(random.randint(USER_ID + 1, USER_ID + 10))

def generate_message(message: str, sender_id: str=None, recipient_id: str= None) -> Message:
    return Message(
        sender_id=sender_id or 'user_' + str(USER_ID),
        recipient_id=recipient_id or generate_user_id(),
        message=message
    )

# Перебираем словарь с сообщениями чтобы наполнить топик 
@app.task
async def send_messages():
    for message in chat_messages:
        try:
            # Создаем случайное сообщение
            msg = generate_message(message)
            time.sleep(5)
            # Отправляем сообщение
            await messages_topic.send(key=msg.recipient_id, value=msg)
            logging.info(f"{msg.sender_id} отправил сообщение сообщение {msg.recipient_id}")
        except:
            logging.error(f"Не удалось отправить сообщение от user_{USER_ID}", exc_info=True)

if __name__ == '__main__':
    app.main()