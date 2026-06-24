from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.data.source.local.sql_alchemy_base import SqlAlchemyBase


class OtpModel(SqlAlchemyBase):
    """SQLAlchemy model for OTP persistence."""

    __tablename__ = "auth_otps"
    # Índice compuesto que respalda find_valid (creado en la migración b7c8d9e0f1a2).
    __table_args__ = (
        Index(
            "ix_auth_otps_lookup",
            "user_id",
            "purpose",
            "code_hash",
            "used_at",
            "expires_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
