from typing import Optional
from datetime import datetime

class Order:
    def __init__(
        self,
        order_id: int,
        order_status: str,
        order_date: str,
        customer_id: int,
        created_at: datetime = datetime.now(),
        updated_at: datetime = datetime.now(),
        deleted_at: Optional[datetime] = None,
    ):
        self.order_id: int = order_id
        self.order_status: str = order_status
        self.order_date: str = order_date
        self.customer_id: int = customer_id
        self.created_at: datetime = created_at
        self.updated_at: datetime = updated_at
        self.deleted_at: Optional[datetime] = deleted_at
        
    def to_dict(self):
        return {
            "order_id": self.order_id,
            "order_status": self.order_status,
            "order_date": self.order_date,
            "customer_id": self.customer_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else ''
        }