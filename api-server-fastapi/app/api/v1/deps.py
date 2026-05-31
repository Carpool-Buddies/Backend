from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from app.core.database import get_session
from app.core.security import decode_token
from app.models.user import User
from app.services import users as user_service

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(token)
    if payload.get("type") != "access" or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = user_service.get_by_id(session, payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user
