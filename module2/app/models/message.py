import faust
from datetime import datetime

class Message(faust.Record):
    
    sender_id: str
    recipient_id: str
    message: str
    created_at: datetime = datetime.now()

    def to_dict(self):
        return {
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "message": self.message,
            "created_at": self.created_at.isoformat()
        }
    
    @staticmethod
    def from_dict(cls, dict_msg):
        return Message(
                sender_id=dict_msg.get("sender_id"),
                recipient_id=dict_msg.get("recipient_id"),
                message=dict_msg.get("message"),
                created_at=dict_msg.get("created_at"),
            )