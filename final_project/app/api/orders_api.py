import asyncio
import os
import json
import logging
import time
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer

from confluent_kafka import Producer

from orders_generator import generate_order
from models import Product
from database import get_db


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-1:9093")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
KAFKA_ORDERS_TOPIC = os.getenv("KAFKA_ORDERS_TOPIC", "orders")
KAFKA_SEARCH_TOPIC = os.getenv("KAFKA_SEARCH_TOPIC", "search")

config = {
       "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,

       # Настройки безопасности SASL_SSL
       "security.protocol": "SASL_SSL",
       "ssl.ca.location": "ssl/ca.crt",  # Сертификат центра сертификации
       "ssl.certificate.location": "ssl/kafka-1.crt",  # Сертификат клиента Kafka
       "ssl.key.location": "ssl/kafka-1.key",  # Приватный ключ для клиента Kafka

       # Настройки SASL-аутентификации
       "sasl.mechanism": "PLAIN",  # Используемый механизм SASL (PLAIN)
       "sasl.username": "producer",  # Имя пользователя для аутентификации
       "sasl.password": "producer-secret",  # Пароль пользователя для аутентификации

       # идентификатор продюсера
       "client.id": "orders-producer",
}

# функция чтения подготовленной AVRO схемы для последующей регистрации
def load_avro_schema_from_file(schema_path):
    with open(schema_path) as f:
        schema_str = f.read()
    return schema_str

# Регистрация схемы и получение schema_id
def register_avro_schema(schema_registry_client, subject, schema_str):
    try:
        latest = schema_registry_client.get_latest_version(subject)
        logging.info(f"Schema is already registered for {subject}:\n{latest.schema.schema_str}")
    except Exception:
        try:
            schema_id = schema_registry_client.register_schema(subject, Schema(schema_str, schema_type='AVRO'))
            return schema_id
        except Exception as e:
            logging.error(f"Ошибка при регистрации схемы: {e}")
            raise

def delivery_report(err, msg):
    if err:
        logging.error(f'❌ Сообщение не доставлено: {err}')
    else:
        logging.info(f'✅ Сообщение отправлено: topic={msg.topic()} | partition={msg.partition()} | key={msg.key().decode("utf-8")}')

orders_schema_str = load_avro_schema_from_file('orders_schema.json')
search_schema_str = load_avro_schema_from_file('search_schema.json')
orders_subject = f'{KAFKA_ORDERS_TOPIC}-value'
search_subject = f'{KAFKA_SEARCH_TOPIC}-value'

producer = Producer(config)

schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})

schema_id_orders = register_avro_schema(schema_registry_client,orders_subject,orders_schema_str)
schema_id_search = register_avro_schema(schema_registry_client,search_subject,search_schema_str)

orders_avro_serializer = AvroSerializer(schema_registry_client,orders_schema_str)
search_avro_serializer = AvroSerializer(schema_registry_client,search_schema_str)
string_serializer = StringSerializer('utf_8')

app = FastAPI(
    title="CLIENT API",
    description="CLIENT API для финального проекта Kafka",
    version="0.1.0"
)


recommendations_db = {
    1: ["iphone_15", "airpods"],
    2: ["macbook_pro"]
}

# для теста работы
@app.get("/")
def read_root():
    return {"Hello": "World"}

# метод создания заказа
@app.post("/orders")
async def create_order(order_id: int, customer_id: int):
    """
    Создать новый заказ
    """
    try:
        order =  next(generate_order(order_id, customer_id))
        order_id = order['order_id']
        producer.produce(
                topic=KAFKA_ORDERS_TOPIC,
                key=string_serializer(order_id),
                value=orders_avro_serializer(order, SerializationContext(KAFKA_ORDERS_TOPIC, MessageField.VALUE)),
                callback=delivery_report
        )
        producer.poll(0)

        return {"message": "Заказ успешно отправлен в Kafka", "order_id": order["order_id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке в Kafka: {str(e)}")

# логируем поиск в кафку
def produce_search_info(customer_id:int, name:str = None, category:str = None):
    try:
        timestamp_str = datetime.now(timezone.utc).isoformat()
        search_query = {"user_id": f"CUST-{customer_id}", "search_ts": timestamp_str}
        if name:
            search_query["name"] = name
        if category:
            search_query["category"] = category

        producer.produce(
                topic=KAFKA_SEARCH_TOPIC,
                value=search_avro_serializer(search_query, SerializationContext(KAFKA_SEARCH_TOPIC, MessageField.VALUE)),
                callback=delivery_report
        )
        producer.poll(0)

    except Exception as e:
        logging.error(f"Не удалось сохранить поиск: {str(e)}")

@app.get("/products", response_model=list[Product])
async def find_product(
    customer_id: int = 1,
    name: str = None,
    category: str = None,
    db: AsyncSession = Depends(get_db),
):
    if not name and not category:
        raise HTTPException(status_code=400, detail="Укажите имя или категорию для поиска")

    # produce_search_info(customer_id, name, category)
    await asyncio.to_thread(produce_search_info, customer_id, name, category)

    query = "SELECT * FROM public.products WHERE 1=1"
    params = {}

    if name:
        query += " AND name ILIKE '%' || :name || '%'"
        params["name"] = name

    if category:
        query += " AND category ILIKE '%' || :category || '%'"
        params["category"] = category

    result = await db.execute(text(query), params)
    rows = result.mappings().all()
    
    if not rows:
        raise HTTPException(status_code=404, detail="Товары не найдены")

    return [dict(row) for row in rows]


@app.get("/recommendations")
async def get_recommendations(db: AsyncSession = Depends(get_db)):
    """
    Получить список рекомендаций для клиента
    """
    query = "SELECT * FROM public.top_products WHERE 1=1"

    result = await db.execute(text(query))
    rows = result.mappings().all()

    if not rows:
        raise HTTPException(status_code=404, detail="Рекомендаций нет")
    
    return [dict(row) for row in rows]