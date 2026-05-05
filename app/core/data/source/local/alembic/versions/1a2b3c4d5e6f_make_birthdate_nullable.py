"""make birthdate nullable for google users

Revision ID: make_birthdate_nullable
Revises: fe8f9c0d1b3e_add_google_id_nullable_password
Create Date: 2026-05-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: str | None = "fe8f9c0d1b3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "birthdate",
        existing_type=sa.Date(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "birthdate",
        existing_type=sa.Date(),
        nullable=False,
    )
