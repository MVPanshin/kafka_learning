import uuid


from confluent_kafka import Consumer
from hdfs import InsecureClient




if __name__ == "__main__":
   consumer_conf = {
       "bootstrap.servers": "kafka-1:9092",
       "group.id": "hadoop-consumer-group",
       "auto.offset.reset": "earliest",
       "enable.auto.commit": True,
       "session.timeout.ms": 6_000,
   }
   consumer = Consumer(consumer_conf)


   consumer.subscribe(["hadoop-topic"])


   # Инициализация HDFS Hadoop клиента
   hdfs_client = InsecureClient("http://hadoop-namenode:9000", user="root")


   try:
       while True:
           msg = consumer.poll(0.1)


           if msg is None:
               continue
           if msg.error():
               print(f"Ошибка: {msg.error()}")
               continue


           value = msg.value().decode("utf-8")
           print(
               f"Получено сообщение: {value=}, "
               f"partition={msg.partition()}, offset={msg.offset()}"
           )


           # Запись сообщения, как файл, в HDFS
           hdfs_file = f"data/message_{uuid.uuid4()}"
           with hdfs_client.write(hdfs_file, encoding="utf-8") as writer:
               writer.write(value + "\n")
           print(f"Сообщение '{value=}' записано в HDFS по пути '{hdfs_file}'")


           # Чтение файла из HDFS для проверки
           with hdfs_client.read(hdfs_file, encoding="utf-8") as reader:
               content = reader.read()
           print(f"Чтение файла '{hdfs_file}' из HDFS. Содержимое файла: '{content.strip()}'")
   finally:
       consumer.close()