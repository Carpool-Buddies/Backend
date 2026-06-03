import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    full_name: str
    avatar_url: str | None = None

    # University code from app.core.universities (e.g. "BGU"); None if unrecognized.
    org: str | None = Field(default=None, index=True)

    # OAuth identity: provider ("google" | "microsoft") + the provider's stable
    # subject id. The pair is unique so the same person can't be linked twice.
    auth_provider: str
    provider_sub: str = Field(index=True)

    # False until the user finishes onboarding (confirms name / org).
    onboarded: bool = Field(default=False)
    is_active: bool = Field(default=True)

    # Aggregate rating, recomputed whenever a new rating is left.
    rating_avg: float = Field(default=0.0)
    rating_count: int = Field(default=0)

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
