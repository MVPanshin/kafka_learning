import os
import faust
import json

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
    value_serializer="json"
)

# Входной и выходной топики
users_topic = app.topic("customers.public.users", key_type=str, value_type=bytes)
orders_topic = app.topic("customers.public.orders", key_type=str, value_type=bytes)

# Чтение топка с пользователями
@app.agent(users_topic)
async def process_users(stream):
    async for event in stream:
        try:
            data = event # json.loads(event.decode('utf-8'))

            # Извлекаем payload
            payload = data.get('payload', {})
            
            # Выводим информацию о сообщении
            logging.info(f"USER - Operation: {payload.get('__op')}")
            logging.info(f"USER - Payload: {payload}")
        except: 
            logging.error(f"Не удалось обработать сообщение от Debezium для таблицы USERS", exc_info=True)

# Чтение топка с заказами
@app.agent(orders_topic)
async def process_orders(stream):
    async for event in stream:
        try:
            data = event # json.loads(event.decode('utf-8'))

            # Извлекаем payload
            payload = data.get('payload', {})
            
            # Выводим информацию о сообщении
            logging.info(f"ORDER - Operation: {payload.get('__op')}")
            logging.info(f"ORDER - Payload: {payload}")
        except: 
            logging.error(f"Не удалось обработать сообщение от Debezium для таблицы ORDERS", exc_info=True)


if __name__ == '__main__':
    app.main()