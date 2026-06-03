from uuid import UUID

from sqlmodel import Session, select, func

from app.models.ride import Ride, RideRequest
from app.models.rating import Rating
from app.models.user import User
from app.schemas.rating import RatingCreate
from app.services import notifications as notif_service


def _was_participant(session: Session, ride: Ride, user_id: UUID) -> bool:
    if ride.driver_id == user_id:
        return True
    req = session.exec(
        select(RideRequest)
        .where(RideRequest.ride_id == ride.id)
        .where(RideRequest.passenger_id == user_id)
        .where(RideRequest.status == "accepted")
    ).first()
    return req is not None


def create_rating(session: Session, ride_id: UUID, rater: User, data: RatingCreate) -> Rating:
    ride = session.get(Ride, ride_id)
    if not ride:
        raise ValueError("Ride not found")
    if ride.status != "completed":
        raise ValueError("Can only rate completed rides")
    if data.ratee_id == rater.id:
        raise ValueError("Cannot rate yourself")

    # Both rater and ratee must have been part of this ride.
    if not _was_participant(session, ride, rater.id):
        raise PermissionError("You were not part of this ride")
    if not _was_participant(session, ride, data.ratee_id):
        raise ValueError("Ratee was not part of this ride")

    existing = session.exec(
        select(Rating)
        .where(Rating.ride_id == ride_id)
        .where(Rating.rater_id == rater.id)
        .where(Rating.ratee_id == data.ratee_id)
    ).first()
    if existing:
        raise ValueError("Already rated this user for this ride")

    rating = Rating(
        ride_id=ride_id,
        rater_id=rater.id,
        ratee_id=data.ratee_id,
        score=data.score,
        comment=data.comment,
    )
    session.add(rating)
    session.commit()
    session.refresh(rating)

    _recompute_user_rating(session, data.ratee_id)

    notif_service.notify(
        session, user_id=data.ratee_id, type="rating_received",
        title="קיבלת דירוג חדש ⭐",
        body=f"{rater.full_name} דירג/ה אותך",
        ride_id=ride_id,
    )
    return rating


def _recompute_user_rating(session: Session, user_id: UUID) -> None:
    avg = session.exec(
        select(func.avg(Rating.score)).where(Rating.ratee_id == user_id)
    ).one()
    count = session.exec(
        select(func.count(Rating.id)).where(Rating.ratee_id == user_id)
    ).one()
    user = session.get(User, user_id)
    if user:
        user.rating_avg = round(float(avg), 2) if avg is not None else 0.0
        user.rating_count = count
        session.add(user)
        session.commit()


def list_for_user(session: Session, user_id: UUID, limit: int = 50) -> list[Rating]:
    return session.exec(
        select(Rating)
        .where(Rating.ratee_id == user_id)
        .order_by(Rating.created_at.desc())
        .limit(limit)
    ).all()
