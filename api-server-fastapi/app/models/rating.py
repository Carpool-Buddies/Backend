import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Rating(SQLModel, table=True):
    __tablename__ = "ratings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ride_id: uuid.UUID = Field(foreign_key="rides.id", index=True)

    # Who gave the rating, and who received it.
    rater_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    ratee_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    score: int  # 1..5
    comment: str | None = None

    created_at: datetime = Field(default_factory=_utcnow)
