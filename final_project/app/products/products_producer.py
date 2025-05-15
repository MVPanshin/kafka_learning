import os
import json
import logging
import time

from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer

from confluent_kafka import Producer

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-1:9093")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
KAFKA_PRODUCTS_TOPIC = os.getenv("KAFKA_PRODUCTS_TOPIC", "products")

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
       "client.id": "products-producer",
   }

# функция чтения подготовленных жисонов, эмулирующих SHOP_API
def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# функция чтения подготовленной AVRO схемы для последующей регистрации
def load_avro_schema_from_file(schema_path):
    with open(schema_path) as f:
        schema_str = f.read()
    return schema_str

# Регистрация схемы и получение schema_id
def register_avro_schema(schema_registry_client, subject, schema_str):
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



if __name__ == "__main__":
   
    producer = Producer(config)
    
    subject = f'{KAFKA_PRODUCTS_TOPIC}-value'

    schema_registry_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
    
    schema_str = load_avro_schema_from_file('products_schema.json')

    try:
       latest = schema_registry_client.get_latest_version(subject)
       logging.info(f"Schema is already registered for {subject}:\n{latest.schema.schema_str}")
    except Exception:
       schema_id = register_avro_schema(schema_registry_client, subject, schema_str)
       logging.info(f"Registered schema for {subject} with id: {schema_id}")

    data = load_data('products_data.json')

    avro_serializer = AvroSerializer(schema_registry_client,schema_str)
    string_serializer = StringSerializer('utf_8')

    for product in data:
        product_id = product['product_id']
        time.sleep(10)
        try:
            producer.produce(
                topic=KAFKA_PRODUCTS_TOPIC,
                key=string_serializer(product_id),
                value=avro_serializer(product, SerializationContext(KAFKA_PRODUCTS_TOPIC, MessageField.VALUE)),
                callback=delivery_report
            )
            producer.poll(0)
        except BufferError:
            logging.warning("⚠️ Очередь Producer заполнена, ждём...")
            producer.flush()
            producer.produce(
                topic=KAFKA_PRODUCTS_TOPIC,
                key=string_serializer(product_id),
                value=avro_serializer(product, SerializationContext(KAFKA_PRODUCTS_TOPIC, MessageField.VALUE)),
                callback=delivery_report
            )

    producer.flush(timeout=10)

    logging.info('Все сообщения отправлены')
