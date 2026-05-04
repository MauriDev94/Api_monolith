"""add google_id and nullable password_hash

Revision ID: add_google_id_nullable_password
Revises: b7c8d9e0f1a2_hash_auth_otps_code
Create Date: 2026-05-04

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_google_id_nullable_password"
down_revision: str | None = "b7c8d9e0f1a2_hash_auth_otps_code"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add google_id column (unique, nullable)
    op.add_column(
        "users",
        sa.Column("google_id", sa.String(255), nullable=True, unique=True),
    )
    # Add google_email_verified column
    op.add_column(
        "users",
        sa.Column(
            "google_email_verified", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")
        ),
    )
    # Make password_hash nullable
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)


def downgrade() -> None:
    # Remove nullable from password_hash
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
    # Remove google columns
    op.drop_column("users", "google_email_verified")
    op.drop_column("users", "google_id")
