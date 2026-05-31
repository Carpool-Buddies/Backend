from fastapi import APIRouter
from app.core.database import engine
from sqlalchemy import text
from app.core.universities import UNIVERSITIES
from app.api.v1.auth import router as auth_router
from app.api.v1.rides import router as rides_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(rides_router)


@router.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}


@router.get("/universities")
def universities():
    return [
        {"code": u.code, "name_he": u.name_he, "name_en": u.name_en}
        for u in UNIVERSITIES
    ]


@router.get("/health/db")
def db_health_check():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
