# Итоговый проект пятого модуля

```
keytool.exe -importcert -alias YandexCA `
   --file $HOME\.kafka\YandexInternalRootCA.crt `
   --keystore $HOME\.kafka\ssl `
   --storepass password `
   --noprompt
```

# Запустите команду получения сообщений из топика:
```
D:\Working\Kafka\kafka-4.0.0-src\bin\windows\kafka-console-consumer.bat `
    --consumer.config adminclient-configs.conf `
    --bootstrap-server <FQDN_брокера>:9091 `
    --topic <имя_топика> `
    --property print.key=true `
    --property key.separator=":"
```

# В отдельном терминале запустите команду отправки сообщения в топик:
```
echo "key:test message" | D:\Working\Kafka\kafka-4.0.0-src\bin\windows\kafka-console-producer.bat `
    --producer.config adminclient-configs.conf `
    --bootstrap-server <FQDN_брокера>:9091 `
    --topic <имя_топика> `
    --property parse.key=true `
    --property key.separator=":"
```    


# Задание №1

## 1. Разворачиваем кафка в Yandex Cloud со следующими характеристиками
```
Имя kafka962
Идентификатор c9q60qns6ama6r9i5d88
Дата создания 25.04.2025, в 12:41
Окружение PRODUCTION
Версия 3.5
Реестр схем данных Да
Kafka Rest API Да
Кластер отказоустойчив Да

Ресурсы
KAFKA 3
Класс хоста s3-c2-m8 (2 vCPU, 100% vCPU rate, 8 ГБ RAM)
Хранилище 32 ГБ network-hdd 

ZOOKEEPER 3
Класс хоста s3-c2-m8 (2 vCPU, 100% vCPU rate, 8 ГБ RAM)
Хранилище 10 ГБ network-ssd 

Сеть 
Облачная сеть default 
Публичный доступ Да

Дополнительные настройки 
Защита от удаления Выключена
```

## 2. Получаем IAM-токен с помощью CLI (у нас настроен профиль, сервисный аккаунт и есть key.json)
```
yc iam create-token
```
Получаем в качестве ответа
```
t1.9euelZqKyJ6dxo6bkZeXncmZjciezO....
```
И записываем его во временную переменную для будущего удобства использования
```
export IAM_TOKEN="t1.9euelZqKyJ6dxo6bkZeXncmZjciezO...."
```

## 3. Создаём топик test_topic с тремя партициями и фактором репликации 3, устанавливаем время жизни сегмент лога как 3 суток, а размер сегмента на 100мб
```
yc managed-kafka topic create test_topic `
  --cluster-id c9q60qns6ama6r9i5d88 `
  --partitions 3 `
  --replication-factor 3 `
  --cleanup-policy delete `
  --retention-ms 259200000 `
  --segment-bytes 104857600
```
Получаем в ответ
```
done (20s)
name: test_topic
cluster_id: c9q60qns6ama6r9i5d88
partitions: "3"
replication_factor: "3"
topic_config_3:
  cleanup_policy: CLEANUP_POLICY_DELETE
  retention_ms: "259200000"
  segment_bytes: "104857600"
```

## 4. Получаем информацию о топике 
```
D:\Working\Kafka\kafka_2.13-4.0.0\bin\windows\kafka-topics.bat `
    --bootstrap-server rc1a-dmsahtc4bddb9cn1.mdb.yandexcloud.net:9091 `
    --topic test_topic `
    --describe `
    --command-config producer-configs.conf
```
Получаем в ответе
```
2025-04-29T14:50:17.265208600Z main ERROR Reconfiguration failed: No configuration found for 'c387f44' at 'null' in 'null'
Topic: test_topic       TopicId: ftYd1yXWRCCkGmWK-RkHQA PartitionCount: 3       ReplicationFactor: 3    Configs: min.insync.replicas=2,cleanup.policy=delete,segment.bytes=104857600,retention.ms=259200000
        Topic: test_topic       Partition: 0    Leader: 1       Replicas: 1,2,3 Isr: 1,2,3      Elr: N/A        LastKnownElr: N/A
        Topic: test_topic       Partition: 1    Leader: 2       Replicas: 2,3,1 Isr: 2,3,1      Elr: N/A        LastKnownElr: N/A
        Topic: test_topic       Partition: 2    Leader: 3       Replicas: 3,1,2 Isr: 3,1,2      Elr: N/A        LastKnownElr: N/A
```

## 5. Создаём пользователей в кластере 
```
yc managed-kafka user create producer `
  --cluster-id c9q60qns6ama6r9i5d88 `
  --password pwd-producer `
  --permission topic=test_topic,role=producer,allow_host=*

yc managed-kafka user create consumer `
  --cluster-id c9q60qns6ama6r9i5d88 `
  --password pwd-consumer `
  --permission topic=test_topic,role=consumer,allow_host=*
```
Получаем ответы
```
done (17s)
name: producer
cluster_id: c9q60qns6ama6r9i5d88
permissions:
  - topic_name: test_topic
    role: ACCESS_ROLE_PRODUCER
    allow_hosts:
      - '*'

done (26s)
name: consumer
cluster_id: c9q60qns6ama6r9i5d88
permissions:
  - topic_name: test_topic
    role: ACCESS_ROLE_CONSUMER
    allow_hosts:
      - '*'
```

## 6. Проверяем инфу о пользователях, и проверяем что информация совпадает
```
yc managed-kafka user get producer --cluster-id c9q60qns6ama6r9i5d88
yc managed-kafka user get consumer --cluster-id c9q60qns6ama6r9i5d88

# или так

curl \
  --request GET \
  --header "Authorization: Bearer $IAM_TOKEN" \
  --url 'https://mdb.api.cloud.yandex.net/managed-kafka/v1/clusters/c9q60qns6ama6r9i5d88/users'
```

## 7. Регистрируем схему данных в Schema Registry
```
curl --cacert YandexInternalRootCA.crt \
  --request POST \
  --header "Content-Type: application/vnd.schemaregistry.v1+json" \
  --user producer:pwd-producer \
  --data @schema-key-flat.json \
  https://rc1a-dmsahtc4bddb9cn1.mdb.yandexcloud.net:443/subjects/test_topic-key/versions

{"id":1}

curl --cacert YandexInternalRootCA.crt \
  --request POST \
  --header "Content-Type: application/vnd.schemaregistry.v1+json" \
  --user producer:pwd-producer \
  --data @schema-value-flat.json \
  https://rc1a-dmsahtc4bddb9cn1.mdb.yandexcloud.net:443/subjects/test_topic-value/versions

{"id":2}
```



## 8. Делаем запрос к Schema Registry для просмотра доступных схем
```
curl --cacert YandexInternalRootCA.crt \
    --request GET \
    --user consumer:pwd-consumer \
    --header "Content-Type: application/json" \
    https://rc1a-dmsahtc4bddb9cn1.mdb.yandexcloud.net:443/subjects

["test_topic-key","test_topic-value"]

----------

curl --cacert YandexInternalRootCA.crt \
    --request GET \
    --url 'https://rc1a-dmsahtc4bddb9cn1.mdb.yandexcloud.net:443/schemas' \
    --user consumer:pwd-consumer \
    --header 'Accept: application/vnd.schemaregistry.v1+json'

[
    {
        "id": 1,
        "schema": "{\"fields\":[{\"name\":\"item_id\",\"type\":\"int\"}],\"name\":\"Key\",\"type\":\"record\"}",
        "schemaType": "AVRO",
        "subject": "test_topic-key",
        "version": 1
    },
    {
        "id": 2,
        "schema": "{\"fields\":[{\"name\":\"name\",\"type\":\"string\"},{\"name\":\"description\",\"type\":\"string\"},{\"name\":\"price\",\"type\":\"double\"}],\"name\":\"Value\",\"type\":\"record\"}",
        "schemaType": "AVRO",
        "subject": "test_topic-value",
        "version": 1
    }
]    

----------

curl --cacert YandexInternalRootCA.crt \
    --request GET \
    --url 'https://rc1a-dmsahtc4bddb9cn1.mdb.yandexcloud.net:443/subjects/test_topic-key/versions' \
    --user consumer:pwd-consumer \
    --header 'Accept: application/vnd.schemaregistry.v1+json'

[1]

----------

curl --cacert YandexInternalRootCA.crt \
    --request GET \
    --url 'https://rc1a-dmsahtc4bddb9cn1.mdb.yandexcloud.net:443/subjects/test_topic-value/versions' \
    --user consumer:pwd-consumer \
    --header 'Accept: application/vnd.schemaregistry.v1+json'

[1]

```


## 9. В powershell Запускаем продюсера для отправки сообщений в топик test_topic (с конфигом пользователя producer)
```
Get-Content data.txt | D:\Working\Kafka\kafka_2.13-4.0.0\bin\windows\kafka-console-producer.bat `
     --bootstrap-server rc1a-dmsahtc4bddb9cn1.mdb.yandexcloud.net:9091 `
     --topic test_topic `
     --property parse.key=true `
     --property key.separator=~ `
     --producer-property acks=all `
     --producer.config producer-configs.conf
```


## 10. Читаем сообщения из топика (с конфигом пользователя consumer)
```
D:\Working\Kafka\kafka_2.13-4.0.0\bin\windows\kafka-console-consumer.bat `
    --bootstrap-server rc1a-dmsahtc4bddb9cn1.mdb.yandexcloud.net:9091 `
    --topic test_topic `
    --property print.key=true `
    --from-beginning `
    --consumer.config consumer-configs.conf

```
Получаеми следующий вывод
```
2025-04-29T14:36:54.197460900Z main ERROR Reconfiguration failed: No configuration found for 'c387f44' at 'null' in 'null'
{"item_id":1}   {"item_id":1, "name":"Item 1", "description": "Description for item 1", "price": 3000.50}
{"item_id":2}   {"item_id":2, "name":"Item 2", "description": "Description for item 2", "price": 2500.00}
{"item_id":4}   {"item_id":3, "name":"Item 4", "description": "Description for item 4", "price": 5000.00}
{"item_id":3}   {"item_id":4, "name":"Item 3", "description": "Description for item 3", "price": 1500.00}
```



# Задание №2

## 1. Поднимаем докер NiFi и postgreSQL
### Идея демонстрации в том, что NiFi читает данные из топика Kafka и складывает их в postgreSQL
### В БД при старте создаётся табличка
```
docker-compose.exe -f .\docker-compose.yaml up -d
```

## 2. Подключаемся к контейнеру c postgres и проверяем что таблица пуста
```
docker exec -it postgres psql -h 127.0.0.1 -U nifi_loader -d mydatabase

mydatabase=> select * from items;

 id | name | description | price
----+------+-------------+-------
(0 rows)

```

## 3. Подключаемся к nifi по адресу http://localhost:8080/nifi/
### Добавляем новую гуппу "Add Process Group" и в выпадающем окне выбираем файл NiFi_Flow_2.json
### В нём находится 2 процессора ConsumeKafkaRecord_2_6 и PutDatabaseRecord 

## 4. В контролерах прописываем необходимые пароли для чувствительных переменных (те, которые не получается задать через параметры)
```
db_user_password=nifi_loader_password
truststorepassword=password
kafka_password=pwd-consumer
```

## 5. В свободном месте кликаем ПКМ и выбираем пункт "Enable all controller services" чтобы включить все контроллеры

## 6. Жмем кнопку запуска потока
### В папке images есть скриншоты происходящего и настроек процессоров

## 7. В консоли запускаем код который наполняет топик в кафке новыми данными
```
Get-Content data2.txt | D:\Working\Kafka\kafka_2.13-4.0.0\bin\windows\kafka-console-producer.bat `
     --bootstrap-server rc1a-dmsahtc4bddb9cn1.mdb.yandexcloud.net:9091 `
     --topic test_topic `
     --property parse.key=true `
     --property key.separator=~ `
     --producer-property acks=all `
     --producer.config producer-configs.conf
```

## 8. Проверяем в БД что данные появились
```
mydatabase=# select count(*) from items
;
 count
-------
    15
(1 row)

mydatabase=# select * from items;
 item_id |  name   |       description       | price
---------+---------+-------------------------+--------
       7 | Item 7  | Description for item 7  |   1500
      11 | Item 11 | Description for item 11 |   1000
      12 | Item 12 | Description for item 12 |    500
      19 | Item 19 | Description for item 19 |   5000
       5 | Item 5  | Description for item 5  | 3000.5
       8 | Item 8  | Description for item 8  |   5000
      13 | Item 13 | Description for item 13 |   1200
      14 | Item 14 | Description for item 14 |    200
      16 | Item 16 | Description for item 16 |     11
      18 | Item 18 | Description for item 18 |   15.2
       6 | Item 6  | Description for item 6  |   2500
       9 | Item 9  | Description for item 9  |   7000
      10 | Item 10 | Description for item 10 |  15000
      15 | Item 15 | Description for item 15 |    333
      17 | Item 17 | Description for item 17 |    5.5
(15 rows)
```

## 9. Убираем за собой
```
docker-compose.exe -f .\docker-compose.yaml down
```