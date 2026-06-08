import uuid
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Ride(SQLModel, table=True):
    __tablename__ = "rides"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    driver_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    origin_address: str
    origin_lat: float | None = None
    origin_lng: float | None = None

    destination_address: str
    dest_lat: float | None = None
    dest_lng: float | None = None

    departure_time: datetime = Field(index=True)
    available_seats: int
    confirmed_passengers: int = Field(default=0)

    price_per_seat: float | None = None
    notes: str | None = None

    # "city_wide" | "org_only"
    visibility: str = Field(default="city_wide", index=True)
    org: str | None = Field(default=None, index=True)

    # "active" | "completed" | "cancelled"
    status: str = Field(default="active", index=True)

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    requests: list["RideRequest"] = Relationship(back_populates="ride")


class RideRequest(SQLModel, table=True):
    __tablename__ = "ride_requests"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ride_id: uuid.UUID = Field(foreign_key="rides.id", index=True)
    passenger_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    requested_seats: int = Field(default=1)
    # "pending" | "accepted" | "rejected" | "cancelled"
    status: str = Field(default="pending", index=True)
    message: str | None = None

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    ride: Ride | None = Relationship(back_populates="requests")
