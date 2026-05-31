from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select

from app.models.ride import Ride, RideRequest
from app.models.user import User
from app.schemas.ride import RideCreate, RideRequestCreate
from app.schemas.user import UserRead
from app.schemas.ride import RideRead, RideRequestRead


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
    return req


def cancel_ride(session: Session, ride_id: UUID, driver: User) -> Ride:
    ride = session.get(Ride, ride_id)
    if not ride or ride.driver_id != driver.id:
        raise PermissionError("Not your ride")
    ride.status = "cancelled"
    ride.updated_at = datetime.now(timezone.utc)
    session.add(ride)
    session.commit()
    session.refresh(ride)
    return ride
