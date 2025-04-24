# Итоговый проект третьего модуля

# Задание №1

## 1. Поднимаем докер с кафкой
```
docker-compose.exe -f .\docker-compose.yaml up -d
```

## 2. Подключаемся к контейнеру и создаём топик
```
docker exec -it kafka-0 bash 
kafka-topics.sh --bootstrap-server localhost:9092 --topic balanced_topic --create --partitions 8 --replication-factor 3 --if-not-exists 
```

## 3. Проверяем балансировку топика
```
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic balanced_topic
```
Получаеми следующий вывод
```
I have no name!@f1f2543b9696:/$ kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic balanced_topic
Topic: balanced_topic   TopicId: rHtA4z3ERdC43KvBJunhcQ PartitionCount: 8       ReplicationFactor: 3    Configs:
         Topic: balanced_topic   Partition: 0    Leader: 3       Replicas: 3,0,1 Isr: 3,0,1
         Topic: balanced_topic   Partition: 1    Leader: 0       Replicas: 0,1,2 Isr: 0,1,2
         Topic: balanced_topic   Partition: 2    Leader: 1       Replicas: 1,2,3 Isr: 1,2,3
         Topic: balanced_topic   Partition: 3    Leader: 2       Replicas: 2,3,0 Isr: 2,3,0
         Topic: balanced_topic   Partition: 4    Leader: 1       Replicas: 1,2,3 Isr: 1,2,3
         Topic: balanced_topic   Partition: 5    Leader: 2       Replicas: 2,3,0 Isr: 2,3,0
         Topic: balanced_topic   Partition: 6    Leader: 3       Replicas: 3,0,1 Isr: 3,0,1
         Topic: balanced_topic   Partition: 7    Leader: 0       Replicas: 0,1,2 Isr: 0,1,2
```

## 4. Создаём файл с конфигом перебалансировки
```
echo '{
    "version": 1,
    "partitions": [
      {"topic": "balanced_topic", "partition": 0, "replicas": [0, 1, 2], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 1, "replicas": [0, 2, 3], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 2, "replicas": [1, 2, 3], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 3, "replicas": [1, 3, 0], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 4, "replicas": [2, 3, 0], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 5, "replicas": [2, 0, 1], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 6, "replicas": [3, 0, 1], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 7, "replicas": [3, 1, 2], "log_dirs": ["any", "any", "any"]}
    ]
}' > tmp/reassignment.json
```
Проверяем, что файлик появился
```
I have no name!@f1f2543b9696:/$ cat ./tmp/reassignment.json
{
    "version": 1,
    "partitions": [
      {"topic": "balanced_topic", "partition": 0, "replicas": [0, 1, 2], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 1, "replicas": [0, 2, 3], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 2, "replicas": [1, 2, 3], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 3, "replicas": [1, 3, 0], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 4, "replicas": [2, 3, 0], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 5, "replicas": [2, 0, 1], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 6, "replicas": [3, 0, 1], "log_dirs": ["any", "any", "any"]},
      {"topic": "balanced_topic", "partition": 7, "replicas": [3, 1, 2], "log_dirs": ["any", "any", "any"]}
    ]
}
```

## 5. Формируем план перераспеределения партиций
```
kafka-reassign-partitions.sh \
--bootstrap-server localhost:9092 \
--broker-list "1,2,3,4" \
--topics-to-move-json-file "/tmp/reassignment.json" \
--generate 
```

## 6. Реализуем план перераспределения партиций
```
kafka-reassign-partitions.sh --bootstrap-server localhost:9092 --reassignment-json-file /tmp/reassignment.json --execute
```
Видим ответ 
```
I have no name!@f1f2543b9696:/$ kafka-reassign-partitions.sh --bootstrap-server localhost:9092 --reassignment-json-file /tmp/reassignment.json --execute
Current partition replica assignment

{"version":1,"partitions":[{"topic":"balanced_topic","partition":0,"replicas":[3,0,1],"log_dirs":["any","any","any"]},{"topic":"balanced_topic","partition":1,"replicas":[0,1,2],"log_dirs":["any","any","any"]},{"topic":"balanced_topic","partition":2,"replicas":[1,2,3],"log_dirs":["any","any","any"]},{"topic":"balanced_topic","partition":3,"replicas":[2,3,0],"log_dirs":["any","any","any"]},{"topic":"balanced_topic","partition":4,"replicas":[1,2,3],"log_dirs":["any","any","any"]},{"topic":"balanced_topic","partition":5,"replicas":[2,3,0],"log_dirs":["any","any","any"]},{"topic":"balanced_topic","partition":6,"replicas":[3,0,1],"log_dirs":["any","any","any"]},{"topic":"balanced_topic","partition":7,"replicas":[0,1,2],"log_dirs":["any","any","any"]}]}

Save this to use as the --reassignment-json-file option during rollback
Successfully started partition reassignments for balanced_topic-0,balanced_topic-1,balanced_topic-2,balanced_topic-3,balanced_topic-4,balanced_topic-5,balanced_topic-6,balanced_topic-7
```

## 7. Проверяем текущее распределение партиций
```
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic balanced_topic
```
Видим ответ 
```
I have no name!@f1f2543b9696:/$ kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic balanced_topic
Topic: balanced_topic   TopicId: rHtA4z3ERdC43KvBJunhcQ PartitionCount: 8       ReplicationFactor: 3    Configs:
        Topic: balanced_topic   Partition: 0    Leader: 0       Replicas: 0,1,2 Isr: 1,0,2
        Topic: balanced_topic   Partition: 1    Leader: 0       Replicas: 0,2,3 Isr: 0,2,3
        Topic: balanced_topic   Partition: 2    Leader: 3       Replicas: 1,2,3 Isr: 3,1,2
        Topic: balanced_topic   Partition: 3    Leader: 0       Replicas: 1,3,0 Isr: 0,1,3
        Topic: balanced_topic   Partition: 4    Leader: 0       Replicas: 2,3,0 Isr: 0,2,3
        Topic: balanced_topic   Partition: 5    Leader: 0       Replicas: 2,0,1 Isr: 0,1,2
        Topic: balanced_topic   Partition: 6    Leader: 3       Replicas: 3,0,1 Isr: 3,0,1
        Topic: balanced_topic   Partition: 7    Leader: 3       Replicas: 3,1,2 Isr: 3,1,2
```
   
## 8. Моделируем сбой. Останавливаем брокер 3 в новом терпинале
```
docker stop kafka-3
```

## 9. Проверяем состояние топика
```
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic balanced_topic
```
Видим, что реплика 3 вышла из списка доступных реплик (Isr)
```
I have no name!@84a841ae5a27:/$ kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic balanced_topic
Topic: balanced_topic   TopicId: rHtA4z3ERdC43KvBJunhcQ PartitionCount: 8       ReplicationFactor: 3    Configs:
        Topic: balanced_topic   Partition: 0    Leader: 0       Replicas: 0,1,2 Isr: 1,0,2
        Topic: balanced_topic   Partition: 1    Leader: 0       Replicas: 0,2,3 Isr: 0,2
        Topic: balanced_topic   Partition: 2    Leader: 1       Replicas: 1,2,3 Isr: 1,2
        Topic: balanced_topic   Partition: 3    Leader: 0       Replicas: 1,3,0 Isr: 0,1
        Topic: balanced_topic   Partition: 4    Leader: 0       Replicas: 2,3,0 Isr: 0,2
        Topic: balanced_topic   Partition: 5    Leader: 0       Replicas: 2,0,1 Isr: 0,1,2
        Topic: balanced_topic   Partition: 6    Leader: 0       Replicas: 3,0,1 Isr: 0,1
        Topic: balanced_topic   Partition: 7    Leader: 1       Replicas: 3,1,2 Isr: 1,2
```

## 10. Возвращаем брокер 3 к жизни
```
docker start kafka-3
```

## 11. Проверяем статус топика
```
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic balanced_topic
```
Видим, что всё нормализовалось
```
I have no name!@84a841ae5a27:/$ kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic balanced_topic
Topic: balanced_topic   TopicId: rHtA4z3ERdC43KvBJunhcQ PartitionCount: 8       ReplicationFactor: 3    Configs:
        Topic: balanced_topic   Partition: 0    Leader: 0       Replicas: 0,1,2 Isr: 1,0,2
        Topic: balanced_topic   Partition: 1    Leader: 0       Replicas: 0,2,3 Isr: 0,2,3
        Topic: balanced_topic   Partition: 2    Leader: 1       Replicas: 1,2,3 Isr: 1,2,3
        Topic: balanced_topic   Partition: 3    Leader: 0       Replicas: 1,3,0 Isr: 0,1,3
        Topic: balanced_topic   Partition: 4    Leader: 0       Replicas: 2,3,0 Isr: 0,2,3
        Topic: balanced_topic   Partition: 5    Leader: 0       Replicas: 2,0,1 Isr: 0,1,2
        Topic: balanced_topic   Partition: 6    Leader: 0       Replicas: 3,0,1 Isr: 0,1,3
        Topic: balanced_topic   Partition: 7    Leader: 1       Replicas: 3,1,2 Isr: 1,2,3
```

## 12. Убираем за собой
```
docker-compose.exe -f .\docker-compose.yaml down
```



# Задание №2

## 1. Поднимаем докер с кафкой
### В папке ssl созданы сертификаты и конфиги для брокеров кафки
### Кластер настроен на использование SSL протокола шифрования и SASL аутентификацией
```
docker-compose.exe -f .\docker-compose-ssl.yaml up -d
```

## 2. Подключаемся к контейнеру
```
docker exec -it kafka-1 bash 
```

## 3. Создаём топики, указывая adminclient-configs.conf (с кредами пользователя admin)
```
kafka-topics --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf --topic topic-1 --create --partitions 3 --replication-factor 2 --if-not-exists
kafka-topics --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf --topic topic-2 --create --partitions 3 --replication-factor 2 --if-not-exists
```

## 4. Проверяем, что топики создались
```
kafka-topics --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf --describe --topic topic-1
kafka-topics --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf --describe --topic topic-2
```
Получаем такие ответы
```
Topic: topic-1  TopicId: XRcLUhTiQ52kKGawiTIYMg PartitionCount: 3       ReplicationFactor: 2    Configs:
        Topic: topic-1  Partition: 0    Leader: 2       Replicas: 2,3   Isr: 2,3
        Topic: topic-1  Partition: 1    Leader: 3       Replicas: 3,1   Isr: 3,1
        Topic: topic-1  Partition: 2    Leader: 1       Replicas: 1,2   Isr: 1,2

Topic: topic-2  TopicId: A1N29Qs8TLa_mS_fXH31ew PartitionCount: 3       ReplicationFactor: 2    Configs:
        Topic: topic-2  Partition: 0    Leader: 2       Replicas: 2,3   Isr: 2,3
        Topic: topic-2  Partition: 1    Leader: 3       Replicas: 3,1   Isr: 3,1
        Topic: topic-2  Partition: 2    Leader: 1       Replicas: 1,2   Isr: 1,2        
```

## 5. Выдаём доступ на топики пользователям producer и consumer
На топик topic-1 обоим на чтение и запись
На топик topic-2 права выдаём только пользователю producer
```
kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:producer \
    --operation read \
    --operation write \
    --operation describe \
    --topic topic-1

kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:producer \
    --operation read \
    --group "*"

kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:consumer \
    --operation read \
    --operation write \
    --operation describe \
    --topic topic-1

kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:consumer \
    --operation read \
    --group "*"

kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf \
    --add --allow-principal User:producer \
    --operation read \
    --operation write \
    --operation describe \
    --topic topic-2
```

## 6. Проверяем какие настройки ACL у кластера сейчас в целом
```
kafka-acls --bootstrap-server kafka-1:9093 --command-config /etc/kafka/secrets/adminclient-configs.conf --list
```
Видим, что наши пользователи получили указанные права
```
Current ACLs for resource `ResourcePattern(resourceType=TOPIC, name=topic-1, patternType=LITERAL)`:
        (principal=User:consumer, host=*, operation=WRITE, permissionType=ALLOW)
        (principal=User:producer, host=*, operation=DESCRIBE, permissionType=ALLOW)
        (principal=User:consumer, host=*, operation=DESCRIBE, permissionType=ALLOW)
        (principal=User:producer, host=*, operation=WRITE, permissionType=ALLOW)
        (principal=User:consumer, host=*, operation=READ, permissionType=ALLOW)
        (principal=User:producer, host=*, operation=READ, permissionType=ALLOW)

Current ACLs for resource `ResourcePattern(resourceType=GROUP, name=*, patternType=LITERAL)`:
        (principal=User:consumer, host=*, operation=READ, permissionType=ALLOW)
        (principal=User:producer, host=*, operation=READ, permissionType=ALLOW)

Current ACLs for resource `ResourcePattern(resourceType=TOPIC, name=topic-2, patternType=LITERAL)`:
        (principal=User:producer, host=*, operation=READ, permissionType=ALLOW)
        (principal=User:producer, host=*, operation=DESCRIBE, permissionType=ALLOW)
        (principal=User:producer, host=*, operation=WRITE, permissionType=ALLOW)

Current ACLs for resource `ResourcePattern(resourceType=CLUSTER, name=kafka-cluster, patternType=LITERAL)`:
        (principal=User:admin, host=*, operation=CLUSTER_ACTION, permissionType=ALLOW)
        (principal=User:admin, host=*, operation=CREATE, permissionType=ALLOW)
```

## 8. Проверим, что producer может писать в topic-1 и topic-2
```
kafka-console-producer --bootstrap-server kafka-1:9093 --topic topic-1 --producer.config /etc/kafka/secrets/producer-configs.conf
```
Отправляем несколько сообщений, печатая текст в консоль, закрываем клиента нажав Crtl+D
Если не возникло ошибок при отправке - всё хорошо, продолжаем
Аналогичным образом отправим несколько сообщений в топик topic-2
```
kafka-console-producer --bootstrap-server kafka-1:9093 --topic topic-2 --producer.config /etc/kafka/secrets/producer-configs.conf
```

## 9. Проверим, что consumer может читать из topic-1
```
kafka-console-consumer --bootstrap-server kafka-1:9093 --topic topic-1 --consumer.config /etc/kafka/secrets/consumer-configs.conf --from-beginning
```
Мы должны увидеть все сообщения, что отправил пользователь producer в топик topic-1
акрываем клиента нажав Crtl+C

## 10. Проверим, что consumer НЕ может читать из topic-2
```
kafka-console-consumer --bootstrap-server kafka-1:9093 --topic topic-2 --consumer.config /etc/kafka/secrets/consumer-configs.conf --from-beginning
```
Мы должны получить сообщение о недостаточности прав доступа к топику topic-2 на чтение
```
[2025-04-24 15:26:55,160] WARN [Consumer clientId=console-consumer, groupId=console-consumer-53512] Error while fetching metadata with correlation id 2 : {topic-2=TOPIC_AUTHORIZATION_FAILED} (org.apache.kafka.clients.NetworkClient)
[2025-04-24 15:26:55,161] ERROR [Consumer clientId=console-consumer, groupId=console-consumer-53512] Topic authorization failed for topics [topic-2] (org.apache.kafka.clients.Metadata)
[2025-04-24 15:26:55,162] ERROR Error processing message, terminating consumer process:  (kafka.tools.ConsoleConsumer$)
org.apache.kafka.common.errors.TopicAuthorizationException: Not authorized to access topics: [topic-2]
Processed a total of 0 messages
```

## 11. Убираем за собой
```
docker-compose.exe -f .\docker-compose-ssl.yaml down
```