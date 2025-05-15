#!/bin/bash

# Отправляем заказы
for ((order_id=1; order_id<=1000; order_id++))
do
    # customer_id от 1 до 100
    customer_id=$(( $RANDOM % 50 + 1 ))

    echo "Отправка заказа: order_id=$order_id, customer_id=$customer_id"

    curl -s -X POST "http://localhost:8085/orders?order_id=$order_id&customer_id=$customer_id"

    # Пауза между запросами (опционально)
    sleep 0.1
done