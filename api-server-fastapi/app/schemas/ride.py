import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator

from app.schemas.user import UserRead


class RideCreate(BaseModel):
    origin_address: str
    destination_address: str
    departure_time: datetime
    available_seats: int
    price_per_seat: float | None = None
    notes: str | None = None
    visibility: str = "city_wide"

    @field_validator("available_seats")
    @classmethod
    def seats_positive(cls, v: int) -> int:
        if v < 1 or v > 8:
            raise ValueError("available_seats must be between 1 and 8")
        return v

    @field_validator("visibility")
    @classmethod
    def valid_visibility(cls, v: str) -> str:
        if v not in ("city_wide", "org_only"):
            raise ValueError("visibility must be city_wide or org_only")
        return v


class RideRequestCreate(BaseModel):
    requested_seats: int = 1
    message: str | None = None

    @field_validator("requested_seats")
    @classmethod
    def seats_positive(cls, v: int) -> int:
        if v < 1 or v > 4:
            raise ValueError("requested_seats must be between 1 and 4")
        return v


class RideRequestRead(BaseModel):
    id: uuid.UUID
    passenger_id: uuid.UUID
    passenger: UserRead | None = None
    requested_seats: int
    status: str
    message: str | None
    created_at: datetime


class RideRead(BaseModel):
    id: uuid.UUID
    driver_id: uuid.UUID
    driver: UserRead | None = None
    origin_address: str
    destination_address: str
    departure_time: datetime
    available_seats: int
    confirmed_passengers: int
    seats_left: int
    price_per_seat: float | None
    notes: str | None
    visibility: str
    org: str | None
    status: str
    created_at: datetime
    # Only populated for the driver viewing their own ride
    requests: list[RideRequestRead] | None = None


class RideRequestUpdate(BaseModel):
    status: str  # "accepted" | "rejected"
