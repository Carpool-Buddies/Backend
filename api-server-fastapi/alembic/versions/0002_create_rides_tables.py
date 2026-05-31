"""create rides and ride_requests tables

Revision ID: 0002_create_rides
Revises: 0001_create_users
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "0002_create_rides"
down_revision: Union[str, None] = "0001_create_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rides",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("origin_address", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("destination_address", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("departure_time", sa.DateTime(), nullable=False),
        sa.Column("available_seats", sa.Integer(), nullable=False),
        sa.Column("confirmed_passengers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("price_per_seat", sa.Float(), nullable=True),
        sa.Column("notes", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("visibility", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="city_wide"),
        sa.Column("org", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rides_driver_id", "rides", ["driver_id"])
    op.create_index("ix_rides_departure_time", "rides", ["departure_time"])
    op.create_index("ix_rides_status", "rides", ["status"])
    op.create_index("ix_rides_visibility", "rides", ["visibility"])
    op.create_index("ix_rides_org", "rides", ["org"])

    op.create_table(
        "ride_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ride_id", sa.Uuid(), nullable=False),
        sa.Column("passenger_id", sa.Uuid(), nullable=False),
        sa.Column("requested_seats", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="pending"),
        sa.Column("message", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ride_id"], ["rides.id"]),
        sa.ForeignKeyConstraint(["passenger_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ride_requests_ride_id", "ride_requests", ["ride_id"])
    op.create_index("ix_ride_requests_passenger_id", "ride_requests", ["passenger_id"])
    op.create_index("ix_ride_requests_status", "ride_requests", ["status"])


def downgrade() -> None:
    op.drop_table("ride_requests")
    op.drop_table("rides")
