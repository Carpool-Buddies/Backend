from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.notification import NotificationRead
from app.services import notifications as notif_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return notif_service.list_for_user(session, user.id)


@router.get("/unread-count", response_model=dict)
def unread_count(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return {"count": notif_service.unread_count(session, user.id)}


@router.post("/{notification_id}/read", response_model=dict)
def mark_read(
    notification_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    ok = notif_service.mark_read(session, user.id, notification_id)
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    return {"status": "ok"}


@router.post("/read-all", response_model=dict)
def mark_all_read(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    n = notif_service.mark_all_read(session, user.id)
    return {"marked": n}
