from confluent_kafka import DeserializingConsumer, serialization
import os

import datetime, random, time
from models.order import Order
from serializers.orderDeserializer import OrderDeserializer

print("Environment variables:")
for key, value in os.environ.items():
    print(f"{key}={value}")

# Чтение переменной окружения
kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka-0:9092")
poll_timeout = float(os.getenv("KAFKA_POLL_TIMEOUT", "1.0"))
group_id = os.getenv("GROUP_ID", "consumer_default")


def get_conf():
    # Конфигурация консюмера – адрес сервера
    conf = {
        "bootstrap.servers": kafka_bootstrap_servers,   # адрес сервера
        "group.id": group_id,                           # Имя группы потребителей
        "key.deserializer": serialization.IntegerDeserializer(),    # Десериализатор ключа
        "value.deserializer": OrderDeserializer(),                  # Десериализатор значения
        "auto.offset.reset": "latest",                              # читаем только новые сообщения
        # "max.poll.records": int(poll_timeout),                      # исключительно, для примера выставляем размер списка равный таймауту
        "fetch.min.bytes": 1024,              # минимальный объём данных (в байтах), который консьюмер должен получить за один запрос к брокеру Kafka
    }

    # По заданию, для консюмера с пуш моделью включаем автокоммит смещений
    if poll_timeout < 10.0:
        conf.update(
            {
                "enable.auto.commit": True,           # Включить автокоммит
                "auto.commit.interval.ms": 5000       # Интервал автокоммита в миллисекундах (5 секунд)
            }
        )
    else:
        conf.update(
            {
                "enable.auto.commit": False,           # Выключить автокоммит
            }
        )

    return conf


def main():
    conf = get_conf()
    autocommit = conf.get("enable.auto.commit", False)

    print(f"Консюмер {group_id} стартует с параметром timeout = {poll_timeout}")

    # Создание потребителя
    consumer = DeserializingConsumer(conf)
    consumer.subscribe(['orders'])
    
    try:
        while True:
            # Получение сообщения
            msg = consumer.poll(poll_timeout)  # Ожидание сообщения в течение poll_timeout

            if msg is None:
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: нет сообщений по таймауту {poll_timeout}")
                continue
            if msg.error():
                print(f"Ошибка при получении сообщения: {msg.error()}")
                continue

            # Получение объекта Order из значения сообщения
            order: Order = msg.value()
            if not autocommit:
                consumer.commit(asynchronous=False)
            
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: новое сообщение: {order.order_id}")
            # print(order.__dict__)
            # print(order.order_id)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Ошибка при чтении топика: {e}")
    finally:
        consumer.close()  



if __name__ == "__main__":
    main()
  