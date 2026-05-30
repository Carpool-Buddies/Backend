from fastapi import APIRouter
from app.core.database import engine
from sqlalchemy import text

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@router.get("/health/db")
def db_health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
