"""add lat/lng coordinates to rides table

Revision ID: 0004_ride_coords
Revises: 0003_notif_ratings
Create Date: 2026-06-08

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004_ride_coords"
down_revision: Union[str, None] = "0003_notif_ratings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("rides", sa.Column("origin_lat", sa.Float(), nullable=True))
    op.add_column("rides", sa.Column("origin_lng", sa.Float(), nullable=True))
    op.add_column("rides", sa.Column("dest_lat", sa.Float(), nullable=True))
    op.add_column("rides", sa.Column("dest_lng", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("rides", "dest_lng")
    op.drop_column("rides", "dest_lat")
    op.drop_column("rides", "origin_lng")
    op.drop_column("rides", "origin_lat")
