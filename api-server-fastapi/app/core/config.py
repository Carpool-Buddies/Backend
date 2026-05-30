from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "CarpoolBuddies"
    DEBUG: bool = False
    SECRET_KEY: str
    FRONTEND_URL: str = "http://localhost:3000"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = "common"

    # Server-side only — never forwarded to frontend
    GOOGLE_MAPS_API_KEY: str = ""

    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@carpoolbuddies.co.il"

    FIREBASE_CREDENTIALS_PATH: str = "firebase-credentials.json"

    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "carpoolbuddies"

    DEFAULT_PICKUP_RADIUS_M: int = 3000
    DEFAULT_TIME_WINDOW_HOURS: int = 2

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
