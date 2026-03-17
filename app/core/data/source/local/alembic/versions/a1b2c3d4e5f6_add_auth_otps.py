"""add auth otps table

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-03-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "auth_otps",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_auth_otps_user_id"), "auth_otps", ["user_id"])
    op.create_index(op.f("ix_auth_otps_purpose"), "auth_otps", ["purpose"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_auth_otps_purpose"), table_name="auth_otps")
    op.drop_index(op.f("ix_auth_otps_user_id"), table_name="auth_otps")
    op.drop_table("auth_otps")
