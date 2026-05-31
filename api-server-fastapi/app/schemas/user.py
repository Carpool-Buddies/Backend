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
    created_at: datetime


class OnboardingUpdate(BaseModel):
    full_name: str
    # Optional override; if omitted we keep the email-detected org.
    org: str | None = None
