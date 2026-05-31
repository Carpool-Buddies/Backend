from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.models.user import User
from app.schemas.ride import RideCreate, RideRead, RideRequestCreate, RideRequestRead, RideRequestUpdate
from app.services import rides as ride_service

router = APIRouter(prefix="/rides", tags=["rides"])


@router.post("", response_model=RideRead, status_code=status.HTTP_201_CREATED)
def create_ride(
    data: RideCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return ride_service.create_ride(session, user, data)


@router.get("", response_model=list[RideRead])
def search_rides(
    destination: str | None = Query(None),
    date: str | None = Query(None, description="YYYY-MM-DD"),
    org_only: bool = Query(False),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return ride_service.search_rides(session, user, destination=destination, date=date, org_only=org_only)


@router.get("/my", response_model=dict)
def my_rides(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return ride_service.get_my_rides(session, user)


@router.get("/{ride_id}", response_model=RideRead)
def get_ride(
    ride_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    ride = ride_service.get_ride(session, ride_id, user)
    if not ride:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ride not found")
    return ride


@router.delete("/{ride_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_ride(
    ride_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        ride_service.cancel_ride(session, ride_id, user)
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your ride")


@router.post("/{ride_id}/requests", response_model=RideRequestRead, status_code=status.HTTP_201_CREATED)
def request_ride(
    ride_id: UUID,
    data: RideRequestCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    try:
        req = ride_service.create_request(session, ride_id, user, data)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return RideRequestRead(
        id=req.id,
        passenger_id=req.passenger_id,
        requested_seats=req.requested_seats,
        status=req.status,
        message=req.message,
        created_at=req.created_at,
    )


@router.patch("/{ride_id}/requests/{request_id}", response_model=RideRequestRead)
def update_request(
    ride_id: UUID,
    request_id: UUID,
    data: RideRequestUpdate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if data.status not in ("accepted", "rejected"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "status must be accepted or rejected")
    try:
        req = ride_service.update_request(session, ride_id, request_id, user, data.status)
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return RideRequestRead(
        id=req.id,
        passenger_id=req.passenger_id,
        requested_seats=req.requested_seats,
        status=req.status,
        message=req.message,
        created_at=req.created_at,
    )
