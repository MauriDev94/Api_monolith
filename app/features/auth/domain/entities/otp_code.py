import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.common.domain_error import DomainError
from app.features.auth.domain.value_objects.otp_purpose import OtpPurpose


@dataclass(slots=True)
class OtpCode:
    """Domain entity representing a one-time password."""

    id: str | None
    user_id: str
    code: str
    purpose: str
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        self._validate()

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at

    def is_used(self) -> bool:
        return self.used_at is not None

    def is_valid(self) -> bool:
        return not self.is_expired() and not self.is_used()

    def consume(self) -> None:
        """Mark OTP as used; raise when already used or expired."""
        if self.is_used():
            raise DomainError("otp has already been used")
        if self.is_expired():
            raise DomainError("otp has expired")
        self.used_at = datetime.now(UTC)

    def _validate(self) -> None:
        if not self.user_id or not self.user_id.strip():
            raise DomainError("otp must be bound to a user")
        if not self.purpose or not self.purpose.strip():
            raise DomainError("otp must have a purpose")
        try:
            OtpPurpose(self.purpose)
        except ValueError as exc:
            raise DomainError(f"invalid otp purpose: '{self.purpose}'") from exc
        if not self.code or len(self.code) != 6 or not self.code.isdigit():
            raise DomainError("otp code must be exactly 6 digits")
        if self.expires_at.tzinfo is None:
            raise DomainError("otp expires_at must be timezone-aware")

    @classmethod
    def create(cls, user_id: str, purpose: str, expire_minutes: int = 10) -> "OtpCode":
        """Factory that generates a secure 6-digit OTP."""
        now = datetime.now(UTC)
        code = f"{secrets.randbelow(1_000_000):06d}"
        return cls(
            id=None,
            user_id=user_id,
            code=code,
            purpose=purpose,
            expires_at=now + timedelta(minutes=expire_minutes),
            created_at=now,
        )
