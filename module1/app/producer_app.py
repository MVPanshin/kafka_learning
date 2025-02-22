from confluent_kafka import SerializingProducer, serialization
import os
import datetime, random, time
from models.order import Order
from serializers.orderSerializer import OrderSerializer

messages_count = int(os.getenv("PRODUCE_MESSAGES", "500"))

# Конфигурация продюсера 
conf = {
    "bootstrap.servers": "kafka-0:9092", # адрес сервера
    "key.serializer": serialization.IntegerSerializer(),  # Сериализатор ключа
    "value.serializer": OrderSerializer(),  # Сериализатор значения
    "acks": "all",  # Для синхронной репликации
    "retries": 3,   # Количество попыток при сбоях
}

# Создание продюсера
producer = SerializingProducer(conf)

def delivery_report(err, msg):
    if err is not None:
        print(f"Ошибка при отправке сообщения: {err}")
    else:
        print(f"Сообщение успешно отправлено в топик {msg.topic()} с offset {msg.offset()}")

# Для тестов
def send_message(n=11, step=10, sleep=0):
    # стартовый ключ сообщений
    i = int(datetime.datetime.now().timestamp())
    for x in range(1, n):
        order = Order(
            order_id = i+x,
            order_status = "pending",
            order_date = datetime.datetime.now().strftime("%Y-%m-%d"),
            customer_id = int(random.random() * 100)
        )
        # принтим то, что будет отправлен
        print(order.__dict__)
        producer.produce(
                topic="orders",
                key=order.order_id,
                value=order,
                on_delivery=delivery_report
            )
        if x % step == 0:
            producer.flush()
            time.sleep(sleep)  # Задержка на sleep секунд
    # Ожидание завершения отправки всех сообщений
    producer.flush()


if __name__ == "__main__":
    
    print("Начинаем отправу сообщений")
    
    # отправляем по 10 сообщений каждые 2 секунды
    send_message(messages_count, 10, 2)

    print("Все сообщения отправлены")
    time.sleep(10)

    while True:
        pass    