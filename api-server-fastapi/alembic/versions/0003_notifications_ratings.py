"""notifications, ratings, user rating columns

Revision ID: 0003_notif_ratings
Revises: 0002_create_rides
Create Date: 2026-06-03

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "0003_notif_ratings"
down_revision: Union[str, None] = "0002_create_rides"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("rating_avg", sa.Float(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"))

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("body", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("ride_id", sa.Uuid(), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ride_id"], ["rides.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_read", "notifications", ["read"])

    op.create_table(
        "ratings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ride_id", sa.Uuid(), nullable=False),
        sa.Column("rater_id", sa.Uuid(), nullable=False),
        sa.Column("ratee_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("comment", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ride_id"], ["rides.id"]),
        sa.ForeignKeyConstraint(["rater_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["ratee_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ratings_ride_id", "ratings", ["ride_id"])
    op.create_index("ix_ratings_rater_id", "ratings", ["rater_id"])
    op.create_index("ix_ratings_ratee_id", "ratings", ["ratee_id"])


def downgrade() -> None:
    op.drop_table("ratings")
    op.drop_table("notifications")
    op.drop_column("users", "rating_count")
    op.drop_column("users", "rating_avg")
