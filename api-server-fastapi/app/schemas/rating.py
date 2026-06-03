import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator


class RatingCreate(BaseModel):
    ratee_id: uuid.UUID
    score: int
    comment: str | None = None

    @field_validator("score")
    @classmethod
    def score_range(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("score must be between 1 and 5")
        return v


class RatingRead(BaseModel):
    id: uuid.UUID
    ride_id: uuid.UUID
    rater_id: uuid.UUID
    ratee_id: uuid.UUID
    score: int
    comment: str | None
    created_at: datetime
