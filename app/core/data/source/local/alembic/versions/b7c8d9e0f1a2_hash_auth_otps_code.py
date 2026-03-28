"""hash auth otp codes

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-28 02:45:00.000000

"""

from __future__ import annotations

from hashlib import sha256
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "auth_otps",
        sa.Column("code_hash", sa.String(length=64), nullable=True),
    )

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, code FROM auth_otps")).fetchall()
    for row in rows:
        code_hash = sha256(str(row.code).encode("utf-8")).hexdigest()
        connection.execute(
            sa.text("UPDATE auth_otps SET code_hash = :code_hash WHERE id = :id"),
            {"id": row.id, "code_hash": code_hash},
        )

    op.alter_column("auth_otps", "code_hash", nullable=False)
    op.drop_column("auth_otps", "code")
    op.create_index(
        "ix_auth_otps_lookup",
        "auth_otps",
        ["user_id", "purpose", "code_hash", "used_at", "expires_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_auth_otps_lookup", table_name="auth_otps")
    op.add_column(
        "auth_otps",
        sa.Column("code", sa.String(length=6), nullable=True),
    )
    op.execute(sa.text("UPDATE auth_otps SET code = '000000' WHERE code IS NULL"))
    op.alter_column("auth_otps", "code", nullable=False)
    op.drop_column("auth_otps", "code_hash")
