import faust
from datetime import datetime

class BlackListMessage(faust.Record):
    
    user_id: str
    target_user_id: str
    is_lock: bool = True
    created_at: datetime = datetime.now()

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "user_id_to_block": self.user_id_to_block,
            "is_lock": self.is_lock,
            "created_at": self.created_at.isoformat()
        }