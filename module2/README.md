# Итоговый проект первого модуля

## 0. Создаём общую сетку
```
docker network create kafka-network
```

## 1. Поднимаем докер с кафкой (топики создаются в инит контейнере)
```
docker-compose -f .\kraft_compose.yaml up -d
```

## 2. Запускаем процесс генерации и обработки сообщений
   - Поднимается 2 подика, которые генерят сообщения (от user_id = "user_1" и user_id = "user_2")
      - Идентификатор пользователя, который генерит сообщение определяется параметром энва - USER_ID
   - Поднимается подик, который занимается обработкой сообщией (фильтрацией по черным спискам и цензурой)
```
docker-compose.exe -f .\faust.yaml up -d
```

## 3. Смотрим что сообщения отправляются в топик `messages`
```
docker logs $(docker ps -a --no-trunc --filter name=faust_writer-1 -q) --follow
```

## 4. Смотрим что сообщения обрабатываются процессором и перенаправляются в топик `filtered_messages`
```
docker logs $(docker ps -a --no-trunc --filter name=faust_message_processor -q) --follow
```

## 5. Вручную добавляем пользователей в черные списки
```
docker exec -it faust_message_processor bash
python3 faust_black_list.py send blocked_users '{"user_id": "user_2", "target_user_id": "user_1", "is_lock": true, "blocked_at": "2025-15-05T15:00:00Z"}' --key "user_2"
python3 faust_black_list.py send blocked_users '{"user_id": "user_3", "target_user_id": "user_1", "is_lock": true, "blocked_at": "2025-15-05T15:00:00Z"}' --key "user_3"
python3 faust_black_list.py send blocked_users '{"user_id": "user_3", "target_user_id": "user_2", "is_lock": true, "blocked_at": "2025-15-05T15:00:00Z"}' --key "user_3"
python3 faust_black_list.py send blocked_users '{"user_id": "user_4", "target_user_id": "user_1", "is_lock": true, "blocked_at": "2025-15-05T15:00:00Z"}' --key "user_4"
python3 faust_black_list.py send blocked_users '{"user_id": "user_5", "target_user_id": "user_1", "is_lock": true, "blocked_at": "2025-15-05T15:00:00Z"}' --key "user_5"
python3 faust_black_list.py send blocked_users '{"user_id": "user_5", "target_user_id": "user_3", "is_lock": true, "blocked_at": "2025-15-05T15:00:00Z"}' --key "user_5"
exit
```

## 6. Проверяем, что списки корректно обработались
```
docker logs $(docker ps -a --no-trunc --filter name=faust_message_processor -q) --follow
```

## 7. Добавляем стоп слова в список
```
docker exec -it faust_message_processor bash
python3 faust_processor_messages.py send @process_bad_words '"капец"'
exit
```

## 8. Проверяем что стоп-слово корректно записалось
```
docker logs $(docker ps -a --no-trunc --filter name=faust_message_processor -q) --follow
```

## 9. Отправляем сообщение со стоп словом
```
docker exec -it faust_message_processor bash
python3 faust_processor_messages.py send messages '{"sender_id": "user_2", "recipient_id": "user_1", "message": "Это было капец как смело!"}' --key "user_1"
exit
```

## 10. Проверяем, что сообщение подверглось цензуре
```
docker logs $(docker ps -a --no-trunc --filter name=faust_message_processor -q) --follow
```
   - должно показаться сообщение "Это было *** как смело!"

## 11. Убираем за собой
```
docker-compose.exe -f .\faust.yaml down
docker-compose.exe -f .\kraft_compose.yaml down
```