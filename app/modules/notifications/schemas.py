from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    kind: str
    title: str
    body: str
    payload: dict
    is_read: bool
    delivered_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}
