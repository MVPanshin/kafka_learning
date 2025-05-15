import os
import faust
import ssl
from io import BytesIO

from confluent_kafka.schema_registry import SchemaRegistryClient

from avro.io import DatumReader, BinaryDecoder
import avro.schema

import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-1:9093")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
KAFKA_PRODUCTS_TOPIC = os.getenv("KAFKA_PRODUCTS_TOPIC", "products")
KAFKA_PRODUCTS_CLEAN_TOPIC = os.getenv("KAFKA_PRODUCTS_CLEAN_TOPIC", "products_clean")
SASL_USERNAME= os.getenv("SASL_USERNAME", "")
SASL_PASSWORD= os.getenv("SASL_PASSWORD", "")

# Получаем инфу о авро схеме
subject = f'{KAFKA_PRODUCTS_TOPIC}-value'
schema_registry_client = SchemaRegistryClient({'url': SCHEMA_REGISTRY_URL})
latest_schema = schema_registry_client.get_latest_version(subject)
# Парсим схему и готовим ридера
schema = avro.schema.parse(latest_schema.schema.schema_str)
reader = DatumReader(schema)

# Функция распаковки AVRO сообщения
def decode(msg_value):
    message_bytes = BytesIO(msg_value)
    message_bytes.seek(5)
    decoder = BinaryDecoder(message_bytes)

    product = reader.read(decoder)
    return product

ssl_context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, cafile='ssl/ca.pem')
ssl_context.load_cert_chain('ssl/kafka-1.crt', keyfile='ssl/kafka-1.key')

# Конфигурация Faust-приложения
app = faust.App(
    "products_faust",
    broker=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer='raw',
    broker_credentials=faust.SASLCredentials(
        username=SASL_USERNAME,
        password=SASL_PASSWORD,
        ssl_context=ssl_context,
    ),
)

# Входной и выходной топики
products_topic = app.topic(KAFKA_PRODUCTS_TOPIC, value_type=bytes)
clean_products_topic = app.topic(KAFKA_PRODUCTS_CLEAN_TOPIC)

# Список категорий, которые нельзя продавать
bad_categories = ["оружине","лекарства", "наркотики"]

# Агент перекладки сообщений
@app.agent(products_topic)
async def process(messages):
    async for key, message in messages.items():
        try:
            product = decode(message)
            
            if product['category'] not in bad_categories:
                try:
                    await clean_products_topic.send(key=key, value=message)
                    logging.info(f"Товар {product['name']} успешно отправлен в продажу (в топик {KAFKA_PRODUCTS_CLEAN_TOPIC})")
                except:
                    logging.error(f"Не удалось доставить сообщение с товаром {product}", exc_info=True)
            else:
                logging.warning(f"Товар {product['name']} находится в запрещённой к продаже категории {product['category']}")
        except Exception as e:
            logging.error(f"Не удалось распаковать сообщение Avro: {e}")


# Процессинг стоп слов
@app.agent(value_type=str)
async def process_bad_categories(categories):
    async for bad_category in categories:
        try:
            bad_categories.append(bad_category)
            logging.info(f"Новая категория в стоп листе - {bad_category}")
        except:
            logging.error(f"Не удалось добавить категорию в список запрещенных", exc_info=True)


if __name__ == '__main__':
    app.main()