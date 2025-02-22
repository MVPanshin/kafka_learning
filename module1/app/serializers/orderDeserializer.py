from confluent_kafka.serialization import Deserializer

from models.order import Order

from datetime import datetime
import json
    
class OrderDeserializer(Deserializer):
    def __call__(self, value: bytes, ctx=None) -> Order:
       
        if value is None:
            return None

        try:
            # Декодируем обратно байты в строку
            json_str = value.decode('utf-8')

            # Парсинг JSON-строки в словарь
            order_dict = json.loads(json_str)

            # Преобразование полей дат из строк ISO в объекты datetime
            def parse_datetime(date_str):
                return datetime.fromisoformat(date_str) if date_str else None

            # Создание объекта Order
            order = Order(
                order_id=order_dict.get("order_id"),
                order_status=order_dict.get("order_status"),
                order_date=order_dict.get("order_date"),
                customer_id=order_dict.get("customer_id"),
                created_at=parse_datetime(order_dict.get("created_at")),
                updated_at=parse_datetime(order_dict.get("updated_at")),
                deleted_at=parse_datetime(order_dict.get("deleted_at"))
            )

            return order

        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"Ошибка при попытке десериализации Order: {e}")    