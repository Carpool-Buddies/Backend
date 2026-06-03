import uuid
from datetime import datetime
from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    body: str
    ride_id: uuid.UUID | None = None
    read: bool
    created_at: datetime
