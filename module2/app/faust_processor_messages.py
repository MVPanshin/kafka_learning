import os
import faust
from models.message import Message
from models.black_list_message import BlackListMessage
import datetime, random, time
import re

import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-0:9092")

# Конфигурация Faust-приложения
app = faust.App(
    "processor_messages_app",
    broker=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer="json",
    store='rocksdb://'
)

# Таблица с матрицей стоплистов
black_list_table = app.Table('black_list', default=list, partitions=3)

# Входной и выходной топики
messages_topic = app.topic("messages", key_type=str, value_type=Message)
filtered_messages_topic = app.topic("filtered_messages", key_type=str, value_type=Message)
blocked_users_topic = app.topic("blocked_users", key_type=str, value_type=BlackListMessage)

# Можно было и в таблице нарвеное хранить, но вроде получится тоже самое что и для black_list_table
bad_words = []

# Процессор 1: Проверка по черным спискам
def not_on_blacklist(message: Message) -> Message:
    # Проверяем черные списки каждого пользователя
    if not (message.sender_id in black_list_table[message.recipient_id]):
        return message
    
    logging.info(f"Sender User_{message.sender_id} is blacklisted by User_{message.recipient_id}")
    return None

# Процессор 2: Цензурирование сообщения
def censoring_message(message: Message) -> Message:
    if message is not None:
        if bad_words:
            pattern = r'\b(' + '|'.join(re.escape(word) for word in bad_words) + r')\b'
            # Заменяем найденные слова на ***
            message.message = re.sub(pattern, "***", message.message, flags=re.IGNORECASE)
        return message
    return None

# Процессинг черных листов
@app.agent(blocked_users_topic)
async def process_blacklist(stream):
    async for block_message in stream:
        try:
            black_list = black_list_table[block_message.user_id]

            if block_message.is_lock:
                black_list.append(block_message.target_user_id)
            else:
                black_list.remove(block_message.target_user_id)

            black_list_table[block_message.user_id] = set(black_list)

            logging.info(f"{block_message.user_id} {'added to ' if block_message.is_lock else 'removed from '} black list {block_message.target_user_id}")
            logging.info(f"Текущая матрица черных списков:")
            for user_id, blocked_users in black_list_table.items():
                logging.info(f"{user_id}: {blocked_users}") 
        except: 
            logging.error(f"Не удалось обработать сообщение c блокировкой пользователя {block_message}", exc_info=True)

# Процессинг стоп слов
@app.agent(value_type=str)
async def process_bad_words(words):
    async for bad_word in words:
        try:
            bad_words.append(bad_word)
            logging.info(f"Новое слово в стоп листе - {bad_word}")
        except:
            logging.error(f"Не удалось добавить слово в список запрещенных слов", exc_info=True)

# Процессинг сообщений
@app.task
async def process_messages():
    stream = app.stream(messages_topic, processors=[not_on_blacklist, censoring_message])

    async for message in stream:
        if message is not None:
            try:
                await filtered_messages_topic.send(key=message.recipient_id, value=message)
                logging.info(f"Сообщение {message} успешно отправлено")
            except:
                logging.error(f"Не удалось обработать сообщение {message}", exc_info=True)



if __name__ == '__main__':
    app.main()