from uuid import UUID

from sqlmodel import Session, select, func

from app.models.notification import Notification


def notify(
    session: Session,
    user_id: UUID,
    type: str,
    title: str,
    body: str,
    ride_id: UUID | None = None,
) -> Notification:
    """Create a notification. Commit is the caller's responsibility-free here:
    we commit so callers can fire-and-forget."""
    n = Notification(
        user_id=user_id, type=type, title=title, body=body, ride_id=ride_id
    )
    session.add(n)
    session.commit()
    session.refresh(n)
    return n


def list_for_user(session: Session, user_id: UUID, limit: int = 50) -> list[Notification]:
    return session.exec(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    ).all()


def unread_count(session: Session, user_id: UUID) -> int:
    return session.exec(
        select(func.count(Notification.id))
        .where(Notification.user_id == user_id)
        .where(Notification.read == False)  # noqa: E712
    ).one()


def mark_read(session: Session, user_id: UUID, notification_id: UUID) -> bool:
    n = session.get(Notification, notification_id)
    if not n or n.user_id != user_id:
        return False
    n.read = True
    session.add(n)
    session.commit()
    return True


def mark_all_read(session: Session, user_id: UUID) -> int:
    notes = session.exec(
        select(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.read == False)  # noqa: E712
    ).all()
    for n in notes:
        n.read = True
        session.add(n)
    session.commit()
    return len(notes)
