from pydantic import BaseModel
from typing import Optional

class Product(BaseModel):
    product_id: str
    name: str
    description: Optional[str] = None
    price_amount: float
    price_currency: str
    category: str
    brand: str
    stock_available: int
    stock_reserved: int
    sku: str
    tags: list[str]
    created_at: str
    updated_at: str
    index: str
    store_id: str

    class Config:
        orm_mode = True