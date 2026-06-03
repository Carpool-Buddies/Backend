from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.models.ride import Ride, RideRequest
from app.models.user import User
from app.schemas.ride import RideCreate, RideRequestCreate, RideUpdate
from app.schemas.user import UserRead
from app.schemas.ride import RideRead, RideRequestRead
from app.services import notifications as notif_service


def _user_read(u: User) -> UserRead:
    from app.core.universities import get_university
    uni = get_university(u.org)
    return UserRead(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        avatar_url=u.avatar_url,
        org=u.org,
        org_name_he=uni.name_he if uni else None,
        onboarded=u.onboarded,
        rating_avg=u.rating_avg,
        rating_count=u.rating_count,
        created_at=u.created_at,
    )


def _ride_read(ride: Ride, driver: User, include_requests: bool = False, session: Session | None = None) -> RideRead:
    requests = None
    if include_requests and session:
        reqs = session.exec(select(RideRequest).where(RideRequest.ride_id == ride.id)).all()
        requests = []
        for req in reqs:
            passenger = session.get(User, req.passenger_id)
            requests.append(RideRequestRead(
                id=req.id,
                passenger_id=req.passenger_id,
                passenger=_user_read(passenger) if passenger else None,
                requested_seats=req.requested_seats,
                status=req.status,
                message=req.message,
                created_at=req.created_at,
            ))

    return RideRead(
        id=ride.id,
        driver_id=ride.driver_id,
        driver=_user_read(driver),
        origin_address=ride.origin_address,
        destination_address=ride.destination_address,
        departure_time=ride.departure_time,
        available_seats=ride.available_seats,
        confirmed_passengers=ride.confirmed_passengers,
        seats_left=ride.available_seats - ride.confirmed_passengers,
        price_per_seat=ride.price_per_seat,
        notes=ride.notes,
        visibility=ride.visibility,
        org=ride.org,
        status=ride.status,
        created_at=ride.created_at,
        requests=requests,
    )


def create_ride(session: Session, driver: User, data: RideCreate) -> RideRead:
    ride = Ride(
        driver_id=driver.id,
        origin_address=data.origin_address,
        destination_address=data.destination_address,
        departure_time=data.departure_time,
        available_seats=data.available_seats,
        price_per_seat=data.price_per_seat,
        notes=data.notes,
        visibility=data.visibility,
        org=driver.org if data.visibility == "org_only" else None,
    )
    session.add(ride)
    session.commit()
    session.refresh(ride)
    return _ride_read(ride, driver)


def search_rides(
    session: Session,
    current_user: User,
    destination: str | None = None,
    date: str | None = None,
    org_only: bool = False,
) -> list[RideRead]:
    query = (
        select(Ride)
        .where(Ride.status == "active")
        .where(Ride.departure_time >= datetime.now(timezone.utc))
        .where(Ride.driver_id != current_user.id)
        .order_by(Ride.departure_time)
    )

    if org_only and current_user.org:
        query = query.where(
            (Ride.visibility == "city_wide") |
            ((Ride.visibility == "org_only") & (Ride.org == current_user.org))
        )
    else:
        query = query.where(Ride.visibility == "city_wide")

    if destination:
        query = query.where(Ride.destination_address.ilike(f"%{destination}%"))

    if date:
        from sqlalchemy import cast, Date
        query = query.where(cast(Ride.departure_time, Date) == date)

    rides = session.exec(query.limit(50)).all()
    result = []
    for ride in rides:
        driver = session.get(User, ride.driver_id)
        if driver:
            result.append(_ride_read(ride, driver))
    return result


def get_my_rides(session: Session, user: User) -> dict:
    driving = session.exec(
        select(Ride)
        .where(Ride.driver_id == user.id)
        .order_by(Ride.departure_time.desc())
        .limit(20)
    ).all()

    joined_req_ids = session.exec(
        select(RideRequest.ride_id)
        .where(RideRequest.passenger_id == user.id)
        .where(RideRequest.status == "accepted")
    ).all()

    joined: list[Ride] = []
    for rid in joined_req_ids:
        ride = session.get(Ride, rid)
        if ride:
            joined.append(ride)

    driving_reads = [_ride_read(r, user, include_requests=True, session=session) for r in driving]

    joined_reads = []
    for ride in joined:
        driver = session.get(User, ride.driver_id)
        if driver:
            joined_reads.append(_ride_read(ride, driver))

    return {"driving": driving_reads, "joined": joined_reads}


def get_ride(session: Session, ride_id: UUID, current_user: User) -> RideRead | None:
    ride = session.get(Ride, ride_id)
    if not ride:
        return None
    driver = session.get(User, ride.driver_id)
    if not driver:
        return None
    is_driver = ride.driver_id == current_user.id
    return _ride_read(ride, driver, include_requests=is_driver, session=session)


def create_request(session: Session, ride_id: UUID, passenger: User, data: RideRequestCreate) -> RideRequest:
    ride = session.get(Ride, ride_id)
    if not ride or ride.status != "active":
        raise ValueError("Ride not available")
    if ride.driver_id == passenger.id:
        raise ValueError("Driver cannot join their own ride")
    if ride.available_seats - ride.confirmed_passengers < data.requested_seats:
        raise ValueError("Not enough seats available")

    existing = session.exec(
        select(RideRequest).where(
            RideRequest.ride_id == ride_id,
            RideRequest.passenger_id == passenger.id,
            RideRequest.status.in_(["pending", "accepted"]),
        )
    ).first()
    if existing:
        raise ValueError("Already have an active request for this ride")

    req = RideRequest(
        ride_id=ride_id,
        passenger_id=passenger.id,
        requested_seats=data.requested_seats,
        message=data.message,
    )
    session.add(req)
    session.commit()
    session.refresh(req)

    # Notify the driver of the new request.
    notif_service.notify(
        session,
        user_id=ride.driver_id,
        type="request_received",
        title="בקשת הצטרפות חדשה",
        body=f"{passenger.full_name} ביקש/ה להצטרף לנסיעה ל{ride.destination_address}",
        ride_id=ride.id,
    )
    return req


def update_request(session: Session, ride_id: UUID, request_id: UUID, driver: User, new_status: str) -> RideRequest:
    ride = session.get(Ride, ride_id)
    if not ride or ride.driver_id != driver.id:
        raise PermissionError("Not your ride")

    req = session.get(RideRequest, request_id)
    if not req or req.ride_id != ride_id:
        raise ValueError("Request not found")
    if req.status != "pending":
        raise ValueError("Request already resolved")

    if new_status == "accepted":
        if ride.available_seats - ride.confirmed_passengers < req.requested_seats:
            raise ValueError("Not enough seats")
        ride.confirmed_passengers += req.requested_seats
        session.add(ride)

    req.status = new_status
    req.updated_at = datetime.now(timezone.utc)
    session.add(req)
    session.commit()
    session.refresh(req)

    # Notify the passenger of the decision.
    if new_status == "accepted":
        notif_service.notify(
            session, user_id=req.passenger_id, type="request_accepted",
            title="הבקשה אושרה! 🎉",
            body=f"אושרת לנסיעה ל{ride.destination_address}",
            ride_id=ride.id,
        )
    elif new_status == "rejected":
        notif_service.notify(
            session, user_id=req.passenger_id, type="request_rejected",
            title="הבקשה נדחתה",
            body=f"הבקשה לנסיעה ל{ride.destination_address} נדחתה",
            ride_id=ride.id,
        )
    return req


def _accepted_passenger_ids(session: Session, ride_id: UUID) -> list[UUID]:
    reqs = session.exec(
        select(RideRequest)
        .where(RideRequest.ride_id == ride_id)
        .where(RideRequest.status == "accepted")
    ).all()
    return [r.passenger_id for r in reqs]


def cancel_ride(session: Session, ride_id: UUID, driver: User) -> Ride:
    ride = session.get(Ride, ride_id)
    if not ride or ride.driver_id != driver.id:
        raise PermissionError("Not your ride")
    passengers = _accepted_passenger_ids(session, ride_id)
    ride.status = "cancelled"
    ride.updated_at = datetime.now(timezone.utc)
    session.add(ride)
    session.commit()
    session.refresh(ride)

    for pid in passengers:
        notif_service.notify(
            session, user_id=pid, type="ride_cancelled",
            title="נסיעה בוטלה",
            body=f"הנסיעה ל{ride.destination_address} בוטלה על ידי הנהג",
            ride_id=ride.id,
        )
    return ride


def update_ride(session: Session, ride_id: UUID, driver: User, data: RideUpdate) -> RideRead:
    ride = session.get(Ride, ride_id)
    if not ride or ride.driver_id != driver.id:
        raise PermissionError("Not your ride")
    if ride.status != "active":
        raise ValueError("Only active rides can be edited")

    fields = data.model_dump(exclude_unset=True)
    for key, value in fields.items():
        setattr(ride, key, value)
    # Keep org consistent with visibility.
    if "visibility" in fields:
        ride.org = driver.org if ride.visibility == "org_only" else None
    ride.updated_at = datetime.now(timezone.utc)
    session.add(ride)
    session.commit()
    session.refresh(ride)

    for pid in _accepted_passenger_ids(session, ride_id):
        notif_service.notify(
            session, user_id=pid, type="ride_updated",
            title="פרטי נסיעה עודכנו",
            body=f"הנהג עדכן את הנסיעה ל{ride.destination_address}",
            ride_id=ride.id,
        )
    return _ride_read(ride, driver)


def complete_ride(session: Session, ride_id: UUID, driver: User) -> Ride:
    ride = session.get(Ride, ride_id)
    if not ride or ride.driver_id != driver.id:
        raise PermissionError("Not your ride")
    if ride.status != "active":
        raise ValueError("Only active rides can be completed")
    ride.status = "completed"
    ride.updated_at = datetime.now(timezone.utc)
    session.add(ride)
    session.commit()
    session.refresh(ride)

    for pid in _accepted_passenger_ids(session, ride_id):
        notif_service.notify(
            session, user_id=pid, type="ride_completed",
            title="הנסיעה הושלמה",
            body=f"הנסיעה ל{ride.destination_address} הושלמה. דרגו את הנהג!",
            ride_id=ride.id,
        )
    return ride


def leave_ride(session: Session, ride_id: UUID, passenger: User) -> None:
    """Passenger leaves a ride they were accepted on; frees their seats."""
    req = session.exec(
        select(RideRequest)
        .where(RideRequest.ride_id == ride_id)
        .where(RideRequest.passenger_id == passenger.id)
        .where(RideRequest.status == "accepted")
    ).first()
    if not req:
        raise ValueError("You are not on this ride")

    ride = session.get(Ride, ride_id)
    req.status = "cancelled"
    req.updated_at = datetime.now(timezone.utc)
    session.add(req)
    if ride:
        ride.confirmed_passengers = max(0, ride.confirmed_passengers - req.requested_seats)
        session.add(ride)
    session.commit()

    if ride:
        notif_service.notify(
            session, user_id=ride.driver_id, type="passenger_left",
            title="נוסע ביטל",
            body=f"{passenger.full_name} ביטל/ה את ההשתתפות בנסיעה ל{ride.destination_address}",
            ride_id=ride.id,
        )
