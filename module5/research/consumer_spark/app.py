from pyspark.sql import SparkSession
from pyspark.sql.functions import (
   col,
   count,
   from_json,
)
from pyspark.sql.types import (
   StringType,
   StructField,
   StructType,
)

# Определение схемы JSON-сообщения
schema = StructType([
   StructField("event", StringType(), True),
   StructField("message", StringType(), True),
])


if __name__ == "__main__":
   spark = SparkSession.builder.appName(
       "StreamingAggregator[PySpark]"
   ).master("local[*]").getOrCreate()

   # Чтение данных из Kafka-топика "spark-topic"
   kafka_df = spark.readStream.format("kafka").option(
       "kafka.bootstrap.servers",
       "kafka-1:9092",
   ).option(
       "subscribe",
       "spark-topic",
   ).option(
       "startingOffsets",
       "earliest",
   ).load()

   # Преобразование бинарного value в строку и разбор JSON
   json_df = kafka_df.select(
       from_json(
           col("value").cast("string"),  # Преобразуем бинарные данные в строку
           schema,                       # Используем определенную JSON-схему
       ).alias("data")                   # Даем название "data" для удобства обращения к полям
   ).filter(col("data").isNotNull())     # Фильтруем некорректные (пустые) JSON-записи

   # Извлекаем конкретные поля "event" и "message" из JSON
   parsed_df = json_df.select(
       col("data.event").alias("event"),
       col("data.message").alias("message"),
   )

   # Агрегируем количество событий по типу "event"
   event_count_df = parsed_df.groupBy(
       "event"
   ).agg(
       count("event").alias("counter")
   )

   # Выводим результат в консоль в режиме "complete"
   # (выводим полный агрегированный результат)
   query = event_count_df.writeStream.outputMode(
       "complete"
   ).format(
       "console"
   ).option(
       "truncate",
       "false"
   ).start()

   print("Запуск обработки данных из Kafka...")
   query.awaitTermination()