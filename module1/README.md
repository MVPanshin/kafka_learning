Итоговый проект первого модуля
0. Создаём общую сетку
docker network create kafka-network

1. Поднимаем докер с кафкой
docker-compose -f .\kraft_compose.yaml up -d

2. Подключаемся к одному из брокеров кафки и создаём топик orders
docker exec -it $(docker ps -a --no-trunc --filter name=kafka-1 -q) bash -c "/opt/bitnami/kafka/bin/kafka-topics.sh --create --if-not-exists --topic orders --bootstrap-server localhost:9092 --partitions 3 --replication-factor 2"

3. Запускаем продюсера (оправляет по 10 сообщений каждые 2 секунды. Количество отправляемых сообщений регулируется в producer.yaml, параметр PRODUCE_MESSAGES)
docker-compose -f .\producer.yaml up -d

4. Смотрим что сообщения отправляются
docker logs $(docker ps -a --no-trunc --filter name=producer -q) --follow

5. Запускаем консюмеров
docker-compose -f .\consumers.yaml up -d

6. Читаем логи 1го косюмера (pull-модель, ручной коммит)
docker logs $(docker ps -a --no-trunc --filter name=consumer-1 -q) --follow

6. Читаем логи 2го косюмера (push-модель, автокоммиты)
docker logs $(docker ps -a --no-trunc --filter name=consumer-2 -q) --follow