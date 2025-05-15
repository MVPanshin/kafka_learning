from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode

if __name__ == "__main__":
    spark = SparkSession.builder \
        .appName("TopProducts") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://hadoop-namenode:9000") \
        .config("spark.hadoop.dfs.namenode.http-address", "hadoop-namenode:9870") \
        .config("spark.hadoop.dfs.namenode.kerberos.principal", "dummy") \
        .config("spark.hadoop.mapreduce.job.user.name", "root") \
        .config("spark.hadoop.user.name", "root") \
        .config("spark.driver.extraJavaOptions", "-Divy.home=/tmp/ivy") \
        .config("spark.sql.catalogImplementation", "in-memory") \
        .config("spark.hadoop.fs.hdfs.impl", "org.apache.hadoop.hdfs.DistributedFileSystem") \
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem") \
        .getOrCreate()
    
    input_path = "hdfs://hadoop-namenode:9000/user/root/data/orders"

    df = spark.read \
        .option("multiline", "false") \
        .json(input_path)

    # df.printSchema()
    # df.show(5)

    # Разворачиваем items массив в отдельные строки
    exploded_df = df.withColumn("item", explode(col("items")))

    # Выбираем нужные поля из item
    products_df = exploded_df.select(
    col("item.product_id").alias("product_id"),
    col("item.category").alias("category"),
    col("item.name").alias("name"),
    col("item.brand").alias("brand"),
    col("item.quantity").alias("quantity")
    )

    # Агрегируем: суммируем quantity по продуктам
    top_products_df = products_df.groupBy("product_id","category","name","brand") \
            .sum("quantity") \
            .withColumnRenamed("sum(quantity)", "total_quantity") \
            .orderBy(col("total_quantity").desc())

    # Выводим топ-10 самых продаваемых товаров
    top_products_df.show(10)

    jdbc_url = "jdbc:postgresql://postgres:5432/mydatabase"
    connection_properties = {
        "user": "srv_search",
        "password": "srv_search",
        "driver": "org.postgresql.Driver"
    }

    # Запись в PostgreSQL
    top_products_df.write.jdbc(url=jdbc_url,
            table="top_products",
            mode="overwrite",
            properties=connection_properties)