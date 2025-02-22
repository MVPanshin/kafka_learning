from confluent_kafka.serialization import Serializer

from models.order import Order

import json

class OrderSerializer(Serializer):
    def __call__(self, obj: Order, ctx=None) -> bytes:
        try:
            if not isinstance(obj, Order) or not hasattr(obj, 'to_dict') or not callable(obj.to_dict):
                raise ValueError("Объект должен иметь метод to_dict() для сериализации")
            
            # Сериализуем словарь в JSON-строку
            json_str = json.dumps(obj.to_dict())
            
            # Ретёрним байты
            return json_str.encode("utf-8")
        
        except Exception as e:
            print(f"Ошибка при сериализации объекта: {e}")
            raise