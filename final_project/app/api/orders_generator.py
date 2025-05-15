import json
import random
from datetime import datetime, timedelta
from faker import Faker

# Инициализируем Faker с русской локалью
fake = Faker('ru_RU')

# Список возможных товаров (БД, надо бы заменить будет на БД)
SAMPLE_PRODUCTS = [
    {"product_id": "12345","name": "Умные часы XYZ","category": "Электроника","brand": "XYZ","sku": "XYZ-12345"},
    {"product_id": "12346","name": "Беспроводные наушники AirPods Pro","category": "Электроника","brand": "Apple","sku": "APL-12346"},
    {"product_id": "12347","name": "Планшет Galaxy Tab S9","category": "Электроника","brand": "Samsung","sku": "SAM-12347"},
    {"product_id": "12348","name": "Фитнес-браслет FitBand Lite","category": "Электроника","brand": "FitTech","sku": "FIT-12348"},
    {"product_id": "12349","name": "Электрический чайник SmartBoil 2000W","category": "Бытовая техника","brand": "HomeTech","sku": "HMT-12349"},
    {"product_id": "12350","name": "Ноутбук MacBook Air M2","category": "Электроника","brand": "Apple","sku": "APL-12350"},
    {"product_id": "12351","name": "Телевизор QLED Samsung QE55Q60B","category": "Электроника","brand": "Samsung","sku": "SAM-12351"},
    {"product_id": "12352","name": "Микроволновая печь LG MS-2042TW","category": "Бытовая техника","brand": "LG","sku": "LG-12352"},
    {"product_id": "12353","name": "Рюкзак Tatonka Trail 40","category": "Спорт и отдых","brand": "Tatonka","sku": "TAT-12353"},
    {"product_id": "12354","name": "Игровая консоль PlayStation 5","category": "Электроника","brand": "Sony","sku": "SON-12354"},
    {"product_id": "12355","name": "Телефон OnePlus Nord CE 2","category": "Электроника","brand": "OnePlus","sku": "ONP-12355"},
    {"product_id": "12356","name": "Пылесос Dyson V15 Detect","category": "Бытовая техника","brand": "Dyson","sku": "DYS-12356"},
    {"product_id": "12357","name": "Кофемашина DeLonghi Magnifica","category": "Бытовая техника","brand": "DeLonghi","sku": "DEL-12357"},
    {"product_id": "12358","name": "Гироскутер Razor Hovertrax 2.0","category": "Транспорт","brand": "Razor","sku": "RAZ-12358"},
    {"product_id": "12359","name": "Электросамокат Xiaomi Mi Essential","category": "Транспорт","brand": "Xiaomi","sku": "XIA-12359"},
    {"product_id": "12360","name": "Фотоаппарат Canon EOS R6 Mark II","category": "Электроника","brand": "Canon","sku": "CAN-12360"},
    {"product_id": "12361","name": "Триммер для бороды Philips QT4003","category": "Бытовая техника","brand": "Philips","sku": "PHI-12361"},
    {"product_id": "12362","name": "Увлажнитель воздуха Boneco S450","category": "Бытовая техника","brand": "Boneco","sku": "BON-12362"},
    {"product_id": "12363","name": "Камера видеонаблюдения Xiaomi Mi Home Security Camera 360°","category": "Электроника","brand": "Xiaomi","sku": "XIA-12363"},
    {"product_id": "12364","name": "Спортивные кроссовки Nike Revolution 6","category": "Одежда и обувь","brand": "Nike","sku": "NIK-12364"},
    {"product_id": "12365","name": "Рюкзак Samsonite Proxis","category": "Спорт и отдых","brand": "Samsonite","sku": "SAM-12365"},
    {"product_id": "12366","name": "Электрогриль Redmond RGM-M902S","category": "Бытовая техника","brand": "Redmond","sku": "RED-12366"},
    {"product_id": "12367","name": "Настольная лампа Xiaomi Mijia LED Lamp 1S","category": "Электроника","brand": "Xiaomi","sku": "XIA-12367"},
    {"product_id": "12368","name": "Беговая дорожка Sportop T900","category": "Спорт и отдых","brand": "Sportop","sku": "SPO-12368"},
    {"product_id": "12369","name": "Ноутбук ASUS ZenBook UX425","category": "Электроника","brand": "ASUS","sku": "ASU-12369"}
]

SHIPPING_METHODS = ["Доставка курьером", "Пункт выдачи", "Почта России"]
PAYMENT_METHODS = ["банковская карта", "нал", "по QR-коду"]
ORDER_STATUSES = ["подтверждён", "в обработке", "отправлен", "доставлен"]
SHIPPING_STATUSES = ["в обработке", "готов к отправке", "в пути"]

def generate_order(p_order_id:int, customer_id:int):
    order_id = f"ORD-{p_order_id}"
    customer_id = f"CUST-{customer_id}"

    # Генерация случайного количества товаров в заказе
    items_count = random.randint(1, 5)
    items = []
    total_amount = 0.0

    for _ in range(items_count):
        product = fake.random_element(elements=SAMPLE_PRODUCTS)
        price = round(random.uniform(1000, 100000), 2)
        quantity = random.randint(1, 3)
        total_price = round(price * quantity, 2)

        items.append({
            "product_id": product["product_id"],
            "name": product["name"],
            "sku": product["sku"],
            "brand": product["brand"],
            "category": product["category"],
            "price": price,
            "quantity": quantity,
            "total_price": total_price
        })

        total_amount += total_price

    shipping_cost = round(random.choice([0.00, 299.00, 499.00, 799.00]), 2)
    total_amount += shipping_cost

    order_date = fake.date_between(start_date='-1y', end_date='today')
    estimated_delivery = order_date + timedelta(days=random.randint(1, 10))
    order_date_iso = datetime.combine(order_date, datetime.min.time()).isoformat() + "Z"
    delivery_iso = datetime.combine(estimated_delivery, datetime.min.time()).isoformat() + "Z"

    yield {
        "order_id": order_id,
        "customer_id": customer_id,
        "items": items,
        "total_amount": round(total_amount, 2),
        "shipping": {
            "method": fake.random_element(elements=SHIPPING_METHODS),
            "cost": shipping_cost,
            "estimated_delivery": delivery_iso,
            "status": fake.random_element(elements=SHIPPING_STATUSES)
        },
        "payment": {
            "method": fake.random_element(elements=PAYMENT_METHODS),
            "status": "оплачено",
            "transaction_id": f"TXN-{fake.random_int(min=100000000, max=999999999)}"
        },
        "order_date": order_date_iso,
        "status": fake.random_element(elements=ORDER_STATUSES),
        "notes": fake.sentence(nb_words=10) if fake.boolean(chance_of_getting_true=30) else None
    }


# Пример использования: генерируем 5 заказов
if __name__ == "__main__":
    for i, order in enumerate(generate_order(), start=1):
        print(json.dumps(order, ensure_ascii=False, indent=2))
        if i >= 5:
            break