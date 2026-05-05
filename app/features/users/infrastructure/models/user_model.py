from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.data.source.local.sql_alchemy_base import SqlAlchemyBase


class UserModel(SqlAlchemyBase):
    """SQLAlchemy model for persisted users."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    lastname: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birthdate: Mapped[date] = mapped_column(Date, nullable=False)
    google_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    google_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
