"""create users table

Revision ID: 0001_create_users
Revises:
Create Date: 2026-05-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "0001_create_users"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("avatar_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("org", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("auth_provider", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("provider_sub", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("onboarded", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_org"), "users", ["org"], unique=False)
    op.create_index(
        op.f("ix_users_provider_sub"), "users", ["provider_sub"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_provider_sub"), table_name="users")
    op.drop_index(op.f("ix_users_org"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
