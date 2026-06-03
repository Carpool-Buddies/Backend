import uuid
from datetime import datetime
from pydantic import BaseModel


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: str | None = None
    org: str | None = None
    org_name_he: str | None = None
    onboarded: bool
    rating_avg: float = 0.0
    rating_count: int = 0
    created_at: datetime


class OnboardingUpdate(BaseModel):
    full_name: str
    # Optional override; if omitted we keep the email-detected org.
    org: str | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
