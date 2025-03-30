# Итоговый проект третьего модуля

## 1. Поднимаем докер с кафкой, кафка коннектом, постгресом, прометеусом и гарфаной (таблицы в постгресе создаются при старте контейнера)
```
docker-compose.exe -f .\docker-compose.yaml up -d
```

## 2. Добавляем дебезиум коннектор для считывания изменений из БД
```
curl -sS -X POST -H 'Content-Type: application/json' --data @module3-connector.json http://localhost:8083/connectors
```

## 3. Проверяем статус коннектора
```
curl http://localhost:8083/connectors/pg-connector-module3/status
```

## 4. Подключаемся к БД и сгенерим изменения в таблицах
```
docker exec -it postgres psql -h 127.0.0.1 -U postgres-user -d customers

-- Добавление пользователей
INSERT INTO users (name, email) VALUES ('John Doe', 'john@example.com');
INSERT INTO users (name, email) VALUES ('Jane Smith', 'jane@example.com');
INSERT INTO users (name, email) VALUES ('Alice Johnson', 'alice@example.com');
INSERT INTO users (name, email) VALUES ('Bob Brown', 'bob@example.com');


-- Добавление заказов
INSERT INTO orders (user_id, product_name, quantity) VALUES (1, 'Product A', 2);
INSERT INTO orders (user_id, product_name, quantity) VALUES (1, 'Product B', 1);
INSERT INTO orders (user_id, product_name, quantity) VALUES (2, 'Product C', 5);
INSERT INTO orders (user_id, product_name, quantity) VALUES (3, 'Product D', 3);
INSERT INTO orders (user_id, product_name, quantity) VALUES (4, 'Product E', 4);

-- Удаление заказа
DELETE FROM orders WHERE id = 1;
```

## 5. Запускаем приложение, которое читает сообщение из debezium-топиков для того чтобы проверить, что они наполняются
```
docker-compose.exe -f .\faust.yaml up -d
```

## 6. Читаем логи приложения фауста, чтобы увидеть чтение событий CDC
```
docker logs $(docker ps -a --no-trunc --filter name=faust_processor -q) --follow
```

## 7. Графана и прометеус
   - Прометеус и графана подключены к докер компоузу как было в уроке
   - В контейнер с кафка коннект добавлен jvm-экспортёр метрик дебезиума чтобы они отправлялись в прометеус
   - Для просмотра статуса коннекторов добавлен debezium-ui контейнер (пришлось для него настроить отдельный экспортер метрик jolokia)

## 8. График с метриками дебезиума
   - по адресу http://localhost:3000/ хостится графана
   - в папке \module3\grafana\dashboards есть json файл с дашбордом дебезиума, который показывает количество и статусы коннекторов дебезиума, количество таблиц и событий над ними

## 9. Убираем за собой
```
docker-compose.exe -f .\faust.yaml down
docker-compose.exe -f .\docker-compose.yaml down
```