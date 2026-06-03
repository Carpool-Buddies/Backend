import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    # "request_received" | "request_accepted" | "request_rejected"
    # | "ride_cancelled" | "ride_completed" | "rating_received"
    type: str
    title: str
    body: str

    # Optional deep-link target (e.g. a ride id) for the frontend.
    ride_id: uuid.UUID | None = Field(default=None, foreign_key="rides.id")

    read: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=_utcnow)
