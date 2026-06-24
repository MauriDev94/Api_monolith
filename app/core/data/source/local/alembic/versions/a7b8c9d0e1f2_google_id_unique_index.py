"""reconcile users.google_id: unique constraint -> unique index

Revision ID: a7b8c9d0e1f2
Revises: 9a8b7c6d5e4f
Create Date: 2026-06-24 00:00:00.000000

La migración original creó google_id con `unique=True` (constraint
users_google_id_key), pero el modelo lo declara `unique=True, index=True`
(índice único ix_users_google_id, igual que email). Se alinea la BD al modelo.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: str | Sequence[str] | None = "9a8b7c6d5e4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("users_google_id_key", "users", type_="unique")
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_users_google_id", table_name="users")
    op.create_unique_constraint("users_google_id_key", "users", ["google_id"])
