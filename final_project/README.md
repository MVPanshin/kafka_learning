# Финальный проект обучения
Основные концепты
- В качестве исходного кластера взят кластер из 4го модуля с настроенным SSL-шифрованием 
- В качестве целевого кластера используется обычный кластер кафки без SSL 
- МиррорМейкер2 (на основе кафка коннекта) реплицирует данные между кластерами кафка
- Кафка коннект записывает данные о товарах в бд постгрес для получения актуальной информации о доступных товарах
- Эмуляцией SHOP API выступает python-продюсер, который раз в 30 секунд отправляет в кафка-топик сообщение о покупке товара
- Для эмуляции CLIENT API поднимается FAST API приложение, которое умеет 
    - создавать заказы
    - делать поиск в БД по товарам и категориям и получать детализацию о товарах
    - запрашивать рекомендации то ТОП 10 самых продаваемых товаров 
- python-hdfs приложение читает топики кафки и складыет данные в hdfs для долгосрочного хранения    
- Spark приложение читает данные из hdfs, проводит "аналитику" и складыет инфу о топ 10 самых продаваемых товаров в постгрес

## 1. Поднимаем кластера кафки, приложений и кластер хадупа
```
docker-compose.exe -f .\docker-compose.yaml up -d
docker-compose.exe -f .\docker-compose-apps.yaml up -d
docker-compose.exe -f .\docker-compose-hadoop.yaml up -d
```

## 2. Подключаемся к контейнеру и создаём топики
```
docker exec -it kafka-1 bash
kafka-topics --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf --topic products --create --partitions 3 --replication-factor 3 --if-not-exists
kafka-topics --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf --topic products_clean --create --partitions 3 --replication-factor 3 --if-not-exists
kafka-topics --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf --topic orders --create --partitions 3 --replication-factor 3 --if-not-exists
kafka-topics --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf --topic search --create --partitions 3 --replication-factor 3 --if-not-exists
```

## 3. Разрешаем пользователю producer писать в топки products
```
kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:producer \
    --operation read \
    --operation write \
    --operation describe \
    --topic products

kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:producer \
    --operation read \
    --operation write \
    --operation describe \
    --topic products_clean

kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:producer \
    --operation read \
    --operation write \
    --operation describe \
    --topic orders

kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:producer \
    --operation read \
    --operation write \
    --operation describe \
    --topic search

kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:consumer \
    --operation read \
    --operation describe \
    --topic products

kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:consumer \
    --operation read \
    --operation describe \
    --topic products_clean

kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:consumer \
    --operation read \
    --operation describe \
    --topic search
```
Получаем в ответ 
```
Adding ACLs for resource `ResourcePattern(resourceType=TOPIC, name=products, patternType=LITERAL)`:
        (principal=User:producer, host=*, operation=DESCRIBE, permissionType=ALLOW)
        (principal=User:producer, host=*, operation=WRITE, permissionType=ALLOW)
        (principal=User:producer, host=*, operation=READ, permissionType=ALLOW)

Current ACLs for resource `ResourcePattern(resourceType=TOPIC, name=products, patternType=LITERAL)`:
        (principal=User:producer, host=*, operation=READ, permissionType=ALLOW)
        (principal=User:producer, host=*, operation=DESCRIBE, permissionType=ALLOW)
        (principal=User:producer, host=*, operation=WRITE, permissionType=ALLOW)

... и тд

```

## 4. Запускаем продюсера сообщений и читаем логи
Сначала отправляем сообщения о товарах
```
docker exec -it producer bash
python3 products_producer.py
```
В логах будет что-то такое
```
2025-05-09 07:43:03,179 INFO: HTTP Request: GET http://schema-registry:8081/subjects/products-value/versions/latest "HTTP/1.1 404 Not Found"
2025-05-09 07:43:13,199 INFO: HTTP Request: POST http://schema-registry:8081/subjects/products-value/versions?normalize=False "HTTP/1.1 200 OK"
2025-05-09 07:43:30,200 INFO: Registered schema for products-value with id: 1
2025-05-09 07:43:50,231 INFO: ✅ Сообщение отправлено: topic=products | partition=0 | key=12345
2025-05-09 07:44:00,222 INFO: ✅ Сообщение отправлено: topic=products | partition=1 | key=12346
2025-05-09 07:44:10,231 INFO: ✅ Сообщение отправлено: topic=products | partition=1 | key=12347
2025-05-09 07:44:20,238 INFO: ✅ Сообщение отправлено: topic=products | partition=0 | key=12348
2025-05-09 07:44:30,257 INFO: ✅ Сообщение отправлено: topic=products | partition=2 | key=12349

... 

exit()
exit
```
Затем генерим заказы отправляя curl запросы в CLIENT_API
```
./orders_gen.sh

Отправка заказа: order_id=1, customer_id=10
{"message":"Заказ успешно отправлен в Kafka","order_id":"ORD-1"}Отправка заказа: order_id=2, customer_id=19
{"message":"Заказ успешно отправлен в Kafka","order_id":"ORD-2"}Отправка заказа: order_id=3, customer_id=25
{"message":"Заказ успешно отправлен в Kafka","order_id":"ORD-3"}Отправка заказа: order_id=4, customer_id=28
{"message":"Заказ успешно отправлен в Kafka","order_id":"ORD-4"}Отправка заказа: order_id=5, customer_id=26
{"message":"Заказ успешно отправлен в Kafka","order_id":"ORD-5"}Отправка заказа: order_id=6, customer_id=37
{"message":"Заказ успешно отправлен в Kafka","order_id":"ORD-6"}Отправка заказа: order_id=7, customer_id=5
{"message":"Заказ успешно отправлен в Kafka","order_id":"ORD-7"}Отправка заказа: order_id=8, customer_id=29
{"message":"Заказ успешно отправлен в Kafka","order_id":"ORD-8"}Отправка заказа: order_id=9, customer_id=11
{"message":"Заказ успешно отправлен в Kafka","order_id":"ORD-9"}Отправка заказа: order_id=10, customer_id=50
{"message":"Заказ успешно отправлен в Kafka","order_id":"ORD-10"}

... 

```

## 5. Запускаем процессинг товаров через цензуру категорий
Faust-процессор должен проанализировать сообщения поступающие в топик products, проверить их на запрещенную категорию и переложить в топик products_clean
Можно проверить логи работы и убедиться что сообщения перекладываются в топик products_clean
```
docker-compose.exe -f .\docker-compose-faust.yaml up -d
docker logs products_faust --follow
```

## 6. Проверяем, что схемы успешно создалась в schema-registry
Можно зайти на сайт http://localhost:8081/schemas, в ответе мы должны увидеть что-то вроде такого
```
[
    {"subject":"products-value","version":1,"id":1,"schema":"{\"type\":\"record\",\"name\":\"Product\",\"namespace\":\"com.example.schema\",\"fields\":[{\"name\":\"product_id\",\"type\":\"string\"},{\"name\":\"name\",\"type\":\"string\"},{\"name\":\"description\",\"type\":\"string\"},{\"name\":\"price\",\"type\":{\"type\":\"record\",\"name\":\"Price\",\"fields\":[{\"name\":\"amount\",\"type\":\"double\"},{\"name\":\"currency\",\"type\":\"string\"}]}},{\"name\":\"category\",\"type\":\"string\"},{\"name\":\"brand\",\"type\":\"string\"},{\"name\":\"stock\",\"type\":{\"type\":\"record\",\"name\":\"Stock\",\"fields\":[{\"name\":\"available\",\"type\":\"int\"},{\"name\":\"reserved\",\"type\":\"int\"}]}},{\"name\":\"sku\",\"type\":\"string\"},{\"name\":\"tags\",\"type\":{\"type\":\"array\",\"items\":\"string\"}},{\"name\":\"images\",\"type\":{\"type\":\"array\",\"items\":{\"type\":\"record\",\"name\":\"Image\",\"fields\":[{\"name\":\"url\",\"type\":\"string\"},{\"name\":\"alt\",\"type\":\"string\"}]}}},{\"name\":\"specifications\",\"type\":{\"type\":\"record\",\"name\":\"Specifications\",\"fields\":[{\"name\":\"weight\",\"type\":\"string\"},{\"name\":\"dimensions\",\"type\":\"string\"},{\"name\":\"battery_life\",\"type\":\"string\"},{\"name\":\"water_resistance\",\"type\":\"string\"}]}},{\"name\":\"created_at\",\"type\":\"string\"},{\"name\":\"updated_at\",\"type\":\"string\"},{\"name\":\"index\",\"type\":\"string\"},{\"name\":\"store_id\",\"type\":\"string\"}]}"},
    
    {"subject":"orders-value","version":1,"id":2,"schema":"{\"type\":\"record\",\"name\":\"Order\",\"namespace\":\"com.example.schema\",\"fields\":[{\"name\":\"order_id\",\"type\":\"string\"},{\"name\":\"customer_id\",\"type\":\"string\"},{\"name\":\"items\",\"type\":{\"type\":\"array\",\"items\":{\"type\":\"record\",\"name\":\"OrderItem\",\"fields\":[{\"name\":\"product_id\",\"type\":\"string\"},{\"name\":\"name\",\"type\":\"string\"},{\"name\":\"sku\",\"type\":\"string\"},{\"name\":\"brand\",\"type\":\"string\"},{\"name\":\"category\",\"type\":\"string\"},{\"name\":\"price\",\"type\":\"double\"},{\"name\":\"quantity\",\"type\":\"int\"},{\"name\":\"total_price\",\"type\":\"double\"}]}}},{\"name\":\"total_amount\",\"type\":\"double\"},{\"name\":\"shipping\",\"type\":{\"type\":\"record\",\"name\":\"ShippingDetails\",\"fields\":[{\"name\":\"method\",\"type\":\"string\"},{\"name\":\"cost\",\"type\":\"double\"},{\"name\":\"estimated_delivery\",\"type\":\"string\"},{\"name\":\"status\",\"type\":\"string\"}]}},{\"name\":\"payment\",\"type\":{\"type\":\"record\",\"name\":\"PaymentDetails\",\"fields\":[{\"name\":\"method\",\"type\":\"string\"},{\"name\":\"status\",\"type\":\"string\"},{\"name\":\"transaction_id\",\"type\":\"string\"}]}},{\"name\":\"order_date\",\"type\":\"string\"},{\"name\":\"status\",\"type\":\"string\"},{\"name\":\"notes\",\"type\":[\"null\",\"string\"],\"default\":null}]}"}
]
```

## 7. Включаем репликацию топиков через MirrorMaker 2 (KafkaConnect)
```
curl -X PUT \
-H "Content-Type: application/json" \
--data '{
    "name": "mirror2",
    "connector.class": "org.apache.kafka.connect.mirror.MirrorSourceConnector",
    "replication.policy.class": "org.apache.kafka.connect.mirror.IdentityReplicationPolicy",
    "source.cluster.alias":"source",
    "topics":"products,products_clean,orders,search",
    "source.cluster.bootstrap.servers":"kafka-1:9093",
    "source.cluster.sasl.jaas.config": "org.apache.kafka.common.security.plain.PlainLoginModule required username=\"admin\" password=\"admin-secret\";",
    "source.cluster.security.protocol": "SASL_SSL",
    "source.cluster.sasl.mechanism": "PLAIN",
    "source.cluster.ssl.truststore.location": "/etc/kafka/secrets/kafka-1.truststore.jks",
    "source.cluster.ssl.truststore.password": "your-password",
    "target.cluster.bootstrap.servers":"kafka-destination-1:9192",
    "producer.override.bootstrap.servers":"kafka-destination-1:9192",
    "producer.override.security.protocol": "PLAINTEXT",
    "producer.override.sasl.mechanism": "",
    "offset-syncs.topic.replication.factor":"3",
    "key.converter": "org.apache.kafka.connect.converters.ByteArrayConverter",
    "value.converter": "org.apache.kafka.connect.converters.ByteArrayConverter",
    "value.converter.schema.registry.url": "http://schema-registry:8081",
    "sync.topic.acls.enabled": "true"
}' \
http://localhost:8083/connectors/mirror2/config
```
Получаем в ответ
```
{"name":"mirror2","config":{"name":"mirror2","connector.class":"org.apache.kafka.connect.mirror.MirrorSourceConnector","replication.policy.class":"org.apache.kafka.connect.mirror.IdentityReplicationPolicy","source.cluster.alias":"source","topics":"products,products_clean,orders,search","source.cluster.bootstrap.servers":"kafka-1:9093","source.cluster.sasl.jaas.config":"org.apache.kafka.common.security.plain.PlainLoginModule required username=\"admin\" password=\"admin-secret\";","source.cluster.security.protocol":"SASL_SSL","source.cluster.sasl.mechanism":"PLAIN","source.cluster.ssl.truststore.location":"/etc/kafka/secrets/kafka-1.truststore.jks","source.cluster.ssl.truststore.password":"your-password","target.cluster.bootstrap.servers":"kafka-destination-1:9192","producer.override.bootstrap.servers":"kafka-destination-1:9192","producer.override.security.protocol":"PLAINTEXT","producer.override.sasl.mechanism":"","offset-syncs.topic.replication.factor":"3","key.converter":"org.apache.kafka.connect.converters.ByteArrayConverter","value.converter":"org.apache.kafka.connect.converters.ByteArrayConverter","value.converter.schema.registry.url":"http://schema-registry:8081","sync.topic.acls.enabled":"true"},"tasks":[],"type":"source"}
```

## 8. Рестартуем кафка-коннект
```
docker-compose stop connect
docker-compose up -d --build connect
```

## 9. Проверяем статус коннектора, чуть подождав
```
curl http://localhost:8083/connectors/mirror2/status
```
Спустя немного времени получаем 
```
{"name":"mirror2","connector":{"state":"RUNNING","worker_id":"connect:8083"},"tasks":[{"id":0,"state":"RUNNING","worker_id":"connect:8083"}],"type":"source"}
```

## 10. Подключаемся ко 2му кластеру кафки и проверяем что топики появились и начали реплицироваться
```
docker exec -it kafka-destination-1 bash
kafka-topics --bootstrap-server kafka-destination-1:9192 --list
```
Ожидаемый результат
```
orders
products
products_clean
search
```

## 11. Читаем данные из реплики
```
kafka-console-consumer \
  --bootstrap-server kafka-destination-1:9192 \
  --topic products \
  --from-beginning \
  --property print.key=true \
  --key-deserializer=org.apache.kafka.common.serialization.StringDeserializer \
  --value-deserializer=org.apache.kafka.common.serialization.StringDeserializer
```
Должны увидеть в ответ что-то вроде такого (Авро формат в виде строк)
```
12364
12364rСпортивные кроссовки Nike Revolution 6�Легкие и удобные кроссовки для повседневной носки и тренировок.
ףp���@RUB4Одежда и обувNike�NIK-12364$кроссовки>спортивная обувNikeRhttps://example.com/images/product20.jpg JNike Revolution 6 - вид сбокуbhttps://example.com/images/product20_closeup.jpg 6Детали подошв250g$30cm x 12cm x 10cmN/A$частичная(2023-10-20T10:15:00Z(2023-10-29T11:25:00Zproductsstore_020
12365
12365:Рюкзак Samsonite Proxis�Деловой рюкзак с отделением для ноутбука и эргономичными лямками.
ףp�W�@RUB0Спорт и отдыхSamsoniteP
SAM-12365рюкзакноутбукофисRhttps://example.com/images/product21.jpg PSamsonite Proxis - вид спередиdhttps://example.com/images/product21_interior.jpg ZВнутреннее пространство
1.1kg$32cm x 22cm x 48cmN/да(2023-10-21T12:00:00Z(2023-10-30T13:10:00Zproductsstore_021
12369
12369BНоутбук ASUS ZenBook UX425�Ультратонкий ноутбук с OLED-дисплеем и процессором Intel Core i7.q=
�O�@RUB,ЭлектроникASUS(ASU-12369ноутбукработа$ультрабукRhttps://example.com/images/product25.jpg PASUS ZenBook UX425 - вид сверху\https://example.com/images/product25_open.jpg XОткрытый экран ноутбука
                                                                                                                                                                                                        1.13kg,313mm x 220mm x 13.9mm12 hours
                                                                                                                                                                                                                                             нет(2023-10-25T11:45:00Z(2023-11-03T12:30:00Zproductsstore_025
```

## 12. Запускаем синк-коннектор который будет писать сообщения в postgres
```
curl -X PUT \
-H "Content-Type: application/json" \
--data '{
    "name": "postgres-sink-products",
    "connector.class": "io.confluent.connect.jdbc.JdbcSinkConnector",
    "tasks.max": "1",
    "topics": "products",
    "connection.url": "jdbc:postgresql://postgres:5432/mydatabase",
    "connection.user": "etl_loader",
    "connection.password": "etl_loader",
    "consumer.override.bootstrap.servers": "kafka-destination-1:9192",
    "consumer.override.security.protocol": "PLAINTEXT",
    "table.name.format": "public.products",
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "key.converter.schemas.enable": "false",
    "value.converter": "io.confluent.connect.avro.AvroConverter",
    "value.converter.schema.registry.url": "http://schema-registry:8081",
    "insert.mode": "upsert",
    "pk.mode": "record_key",
    "pk.fields": "product_id",
    "field.names.rename": "",
    "field.type.names": "tags,specifications",
    "field.type.mapping": "tags=TEXT[],specifications=JSONB",
    "transforms": "flatten",
    "transforms.flatten.type": "org.apache.kafka.connect.transforms.Flatten$Value",
    "transforms.flatten.delimiter": "_",
    "fields.whitelist": "product_id,name,description,price_amount,price_currency,category,brand,stock_available,stock_reserved,sku,tags,created_at,updated_at,index,store_id"
}' \
http://localhost:8083/connectors/postgres-sink-products/config

```
Получаем в ответ
```
{"name":"postgres-sink-products","config":{"name":"postgres-sink-products","connector.class":"io.confluent.connect.jdbc.JdbcSinkConnector","tasks.max":"1","topics":"products","connection.url":"jdbc:postgresql://postgres:5432/mydatabase","connection.user":"etl_loader","connection.password":"etl_loader","consumer.override.bootstrap.servers":"kafka-destination-1:9192","consumer.override.security.protocol":"PLAINTEXT","table.name.format":"public.products","key.converter":"org.apache.kafka.connect.storage.StringConverter","key.converter.schemas.enable":"false","value.converter":"io.confluent.connect.avro.AvroConverter","value.converter.schema.registry.url":"http://schema-registry:8081","insert.mode":"upsert","pk.mode":"record_key","pk.fields":"product_id","field.names.rename":"","field.type.names":"tags,specifications","field.type.mapping":"tags=TEXT[],specifications=JSONB","transforms":"flatten","transforms.flatten.type":"org.apache.kafka.connect.transforms.Flatten$Value","transforms.flatten.delimiter":"_","fields.whitelist":"product_id,name,description,price_amount,price_currency,category,brand,stock_available,stock_reserved,sku,tags,created_at,updated_at,index,store_id"},"tasks":[],"type":"sink"}
```

На всякий случай команды для работы с синк коннектором
Бывает, что подтупливает и синхронизация кластеров подтормаживает
```
curl http://localhost:8083/connectors/postgres-sink-products/tasks/0/status
curl -X POST http://localhost:8083/connectors/postgres-sink-products/tasks/0/restart
curl -X DELETE http://localhost:8083/connectors/postgres-sink-products

curl http://localhost:8083/connectors/mirror2/tasks/0/status
curl -X POST http://localhost:8083/connectors/mirror2/tasks/0/restart
curl -X DELETE http://localhost:8083/connectors/mirror2
```


## 13. Проверяем статус коннектора синка в pg
```
curl http://localhost:8083/connectors/postgres-sink-products/status
```
Спустя немного времени получаем 
```
{"name":"postgres-sink-products","connector":{"state":"RUNNING","worker_id":"localhost:8083"},"tasks":[{"id":0,"state":"RUNNING","worker_id":"localhost:8083"}],"type":"sink"}
```


## 14. Подключаемся к postgres и проверяем что данные в таблицах появляются
```
docker exec -it postgres psql -h 127.0.0.1 -U postgres -d mydatabase

mydatabase=# SELECT count(*) from public.products;
 count
-------
    25
(1 row)

```
Если данных нет, нужно рестартануть таску, коннектор или целиком кафка-коннект и повторить пункт 12 с проверкой логов


## 15. Выполняем несколько запросов от имени клиента с поиском товаров
```
curl "http://localhost:8085/products?customer_id=1&name=XY"
```
Получаеми следующий вывод
```
[
    {"product_id":"12345","name":"Умные часы XYZ","description":"Умные часы с функцией мониторинга здоровья, GPS и уведомлениями.","price_amount":4999.99,"price_currency":"RUB","category":"Электроника","brand":"XYZ","stock_available":150,"stock_reserved":20,"sku":"XYZ-12345","tags":["умные часы","гаджеты","технологии"],"created_at":"2023-10-01T12:00:00Z","updated_at":"2023-10-10T15:30:00Z","index":"products","store_id":"store_001"},
    
    {"product_id":"12347","name":"Планшет Galaxy Tab S9","description":"Высокопроизводительный планшет с AMOLED дисплеем и поддержкой S Pen.","price_amount":34999.99,"price_currency":"RUB","category":"Электроника","brand":"Samsung","stock_available":50,"stock_reserved":5,"sku":"SAM-12347","tags":["планшет","Android","Samsung"],"created_at":"2023-10-03T08:00:00Z","updated_at":"2023-10-12T11:00:00Z","index":"products","store_id":"store_003"}
]
```
Дополнительно делаем поиск по категории "Транспорт"
```
curl "http://localhost:8085/products?customer_id=1&category=%D1%82%D1%80%D0%B0%D0%BD%D1%81%D0%BF%D0%BE%D1%80%D1%82"

```
Получаеми следующий вывод
```
[
    {"product_id":"12358","name":"Гироскутер Razor Hovertrax 2.0","description":"Электрический гироскутер с LED-подсветкой и улучшенной батареей.","price_amount":17999.99,"price_currency":"RUB","category":"Транспорт","brand":"Razor","stock_available":50,"stock_reserved":7,"sku":"RAZ-12358","tags":["гироскутер","электротранспорт","движение"],"created_at":"2023-10-14T14:00:00Z","updated_at":"2023-10-23T13:10:00Z","index":"products","store_id":"store_014"},
    
    {"product_id":"12359","name":"Электросамокат Xiaomi Mi Essential","description":"Легкий электросамокат с компактной конструкцией и длительным временем работы.","price_amount":24999.99,"price_currency":"RUB","category":"Транспорт","brand":"Xiaomi","stock_available":40,"stock_reserved":6,"sku":"XIA-12359","tags":["самокат","электросамокат","движение"],"created_at":"2023-10-15T16:20:00Z","updated_at":"2023-10-24T15:30:00Z","index":"products","store_id":"store_015"}
]
```

## 16. Запускаем python-консюмер, который будет складывать данные в hdfs
```
docker-compose.exe -f .\docker-compose-consumer-hdfs.yaml up -d
docker logs consumer-hdfs --follow
```

## 17. Запускаем spark-задачу которая построит статистику по купленным товарам и запросам пользователей и доставит данные до базы постгрес
```
docker exec -it -u root spark-client bash
spark-submit   --driver-class-path /app/drivers/postgresql-42.6.2.jar app2.py
```

## 18. Запрашиваем рекомендации для клиента
```
curl "http://localhost:8085/recommendations"
```
Получаем в ответ ТОП 10 товаров
```
[{"product_id":"12355","category":"Электроника","name":"Телефон OnePlus Nord CE 2","brand":"OnePlus","total_quantity":42},{"product_id":"12351","category":"Электроника","name":"Телевизор QLED Samsung QE55Q60B","brand":"Samsung","total_quantity":29},{"product_id":"12367","category":"Электроника","name":"Настольная лампа Xiaomi Mijia LED Lamp 1S","brand":"Xiaomi","total_quantity":24},{"product_id":"12359","category":"Транспорт","name":"Электросамокат Xiaomi Mi Essential","brand":"Xiaomi","total_quantity":23},{"product_id":"12361","category":"Бытовая техника","name":"Триммер для бороды Philips QT4003","brand":"Philips","total_quantity":23},{"product_id":"12363","category":"Электроника","name":"Камера видеонаблюдения Xiaomi Mi Home Security Camera 360°","brand":"Xiaomi","total_quantity":23},{"product_id":"12357","category":"Бытовая техника","name":"Кофемашина DeLonghi Magnifica","brand":"DeLonghi","total_quantity":22},{"product_id":"12364","category":"Одежда и обувь","name":"Спортивные кроссовки Nike Revolution 6","brand":"Nike","total_quantity":22},{"product_id":"12358","category":"Транспорт","name":"Гироскутер Razor Hovertrax 2.0","brand":"Razor","total_quantity":22},{"product_id":"12345","category":"Электроника","name":"Умные часы XYZ","brand":"XYZ","total_quantity":22},{"product_id":"12354","category":"Электроника","name":"Игровая консоль PlayStation 5","brand":"Sony","total_quantity":22},{"product_id":"12356","category":"Бытовая техника","name":"Пылесос Dyson V15 Detect","brand":"Dyson","total_quantity":20},{"product_id":"12366","category":"Бытовая техника","name":"Электрогриль Redmond RGM-M902S","brand":"Redmond","total_quantity":18},{"product_id":"12353","category":"Спорт и отдых","name":"Рюкзак Tatonka Trail 40","brand":"Tatonka","total_quantity":18},{"product_id":"12368","category":"Спорт и отдых","name":"Беговая дорожка Sportop T900","brand":"Sportop","total_quantity":17},{"product_id":"12346","category":"Электроника","name":"Беспроводные наушники AirPods Pro","brand":"Apple","total_quantity":17},{"product_id":"12347","category":"Электроника","name":"Планшет Galaxy Tab S9","brand":"Samsung","total_quantity":17},{"product_id":"12365","category":"Спорт и отдых","name":"Рюкзак Samsonite Proxis","brand":"Samsonite","total_quantity":15},{"product_id":"12350","category":"Электроника","name":"Ноутбук MacBook Air M2","brand":"Apple","total_quantity":14},{"product_id":"12352","category":"Бытовая техника","name":"Микроволновая печь LG MS-2042TW","brand":"LG","total_quantity":13},{"product_id":"12362","category":"Бытовая техника","name":"Увлажнитель воздуха Boneco S450","brand":"Boneco","total_quantity":11},{"product_id":"12349","category":"Бытовая техника","name":"Электрический чайник SmartBoil 2000W","brand":"HomeTech","total_quantity":10},{"product_id":"12360","category":"Электроника","name":"Фотоаппарат Canon EOS R6 Mark II","brand":"Canon","total_quantity":9},{"product_id":"12348","category":"Электроника","name":"Фитнес-браслет FitBand Lite","brand":"FitTech","total_quantity":6},{"product_id":"12369","category":"Электроника","name":"Ноутбук ASUS ZenBook UX425","brand":"ASUS","total_quantity":4}]
```

## 19. Убираем за собой
```
docker-compose.exe -f .\docker-compose.yaml down --volumes
docker-compose.exe -f .\docker-compose-apps.yaml down --volumes
docker-compose.exe -f .\docker-compose-hadoop.yaml down --volumes
docker-compose.exe -f .\docker-compose-faust.yaml down --volumes
docker-compose.exe -f .\docker-compose-consumer-hdfs.yaml down --volumes
```