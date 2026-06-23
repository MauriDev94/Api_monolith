"""add due_date to todos

Revision ID: 9a8b7c6d5e4f
Revises: 1a2b3c4d5e6f
Create Date: 2026-06-23 00:00:00.000000

Fixes schema drift (O1): TodoModel declara `due_date` y el código lo usa, pero
ninguna migración creaba la columna. En SQLite (metadata.create_all) la columna
aparecía sola; en Postgres (migraciones) no existía y rompía POST/GET /v1/todos.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a8b7c6d5e4f"
down_revision: str | Sequence[str] | None = "1a2b3c4d5e6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "todos",
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("todos", "due_date")
