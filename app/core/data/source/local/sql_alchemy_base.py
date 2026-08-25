"""Shared SQLAlchemy declarative base used by all ORM models.

SQLAlchemy 2.0 idiom: inherit from DeclarativeBase instead of calling the
legacy declarative_base() function, so the type is visible to mypy strict.
The codebase already uses Mapped[T] + mapped_column() everywhere — this just
makes the base match.
"""

from sqlalchemy.orm import DeclarativeBase


class SqlAlchemyBase(DeclarativeBase):
    """Declarative base for all ORM models in the project."""
