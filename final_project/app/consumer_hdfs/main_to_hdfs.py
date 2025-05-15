import uuid
import os
import logging
import time
import json
from io import BytesIO

from confluent_kafka import Consumer, KafkaException, KafkaError
from confluent_kafka.serialization import StringDeserializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka import Consumer
from hdfs import InsecureClient
from avro.io import DatumReader, BinaryDecoder
import avro.schema

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-destination-1:9192")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
HDFS_URI = os.getenv("HDFS_URI", "http://hadoop-namenode:9870")
TOPICS = ['orders', 'search']
HDFS_PATH_TEMPLATE = 'data/{topic}'

# Инициализация HDFS Hadoop клиента
hdfs_client = InsecureClient(HDFS_URI, user="root")

schema_registry_client = SchemaRegistryClient({'url': SCHEMA_REGISTRY_URL})

# Парсим схему и готовим ридера
# latest_schema_orders = schema_registry_client.get_latest_version('orders-value')
# schema_orders = avro.schema.parse(latest_schema_orders.schema.schema_str)
# reader_orders = DatumReader(schema_orders)
# 
# latest_schema_search = schema_registry_client.get_latest_version('search-value')
# schema_search = avro.schema.parse(latest_schema_search.schema.schema_str)
# reader_search = DatumReader(schema_orders)
# 
# reader = {"orders": reader_orders, "search" : reader_search}

avro_deserializer = AvroDeserializer(schema_registry_client)

#  Функция распаковки AVRO сообщения
# def decode_confluent_avro(msg_value, topic):
#     message_bytes = BytesIO(msg_value)
#     message_bytes.seek(5)
#     decoder = BinaryDecoder(message_bytes)
#     
#     try:
#         deserialized = reader.get(topic).read(decoder)
#         return deserialized
#     except Exception as e:
#         logging.error(f"Ошибка десериализации: {e}")
#         return None

def get_hdfs_path(topic: str, customer_id: str):
    # today = datetime.now().strftime("%Y-%m-%d")
    return HDFS_PATH_TEMPLATE.format(topic=topic, customer_id=customer_id)

def write_to_hdfs(topic: str, message: dict):
    customer_id = message.get('customer_id') if topic == 'orders' else message.get('user_id')
    path = get_hdfs_path(topic, customer_id)

    try:
        with hdfs_client.write(path, encoding='utf-8', append=True, overwrite=False) as writer:
            writer.write(json.dumps(message, ensure_ascii=False) + "\n")
        logging.info(f"Записано в HDFS: {path}")
    except Exception as e:
        if "not found" in str(e):
            logging.info(f"Файл не существует → создаём новый: {path}")
            hdfs_client.write(path, data="", overwrite=True)
            write_to_hdfs(topic, message)
        else:
            logging.error(f"Ошибка записи в HDFS: {e}")

def process_message(msg):
    topic = msg.topic()
    value = msg.value()

    if msg.error():
        if msg.error().code() == KafkaError._PARTITION_EOF:
            logging.info(f"Достигнут конец партиции: {msg.partition()}")
        else:
            logging.error(f"Ошибка Kafka: {msg.error()}")
        return

    # decoded = decode_confluent_avro(value, topic)
    decoded = avro_deserializer(
            value,
            SerializationContext(topic, MessageField.VALUE)
    )
    
    logging.info(f"Топик {topic}: {decoded}")
    if decoded:
        write_to_hdfs(topic, decoded)
        time.sleep(1)

def main():
   consumer_conf = {
       "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
       "group.id": "hadoop-consumer-group",
       "auto.offset.reset": "earliest",
       "enable.auto.commit": True,
       "session.timeout.ms": 6_000,
   }
   consumer = Consumer(consumer_conf)
   consumer.subscribe(TOPICS)

   try:
       while True:
           msg = consumer.poll(0.1)

           if msg is None:
               continue
           if msg.error():
               print(f"Ошибка: {msg.error()}")
               continue

           process_message(msg)    
           
   finally:
       consumer.close()


if __name__ == "__main__":
   main()