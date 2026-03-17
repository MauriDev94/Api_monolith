from abc import ABC, abstractmethod

from app.features.auth.domain.entities.otp_code import OtpCode


class OtpDatasource(ABC):
    """Application port for OTP persistence and lookup."""

    @abstractmethod
    def save(self, otp: OtpCode) -> OtpCode:
        """Persist a new or updated OTP."""
        pass

    @abstractmethod
    def find_valid(self, user_id: str, code: str, purpose: str) -> OtpCode | None:
        """Return a valid, non-expired and non-used OTP, or None."""
        pass

    @abstractmethod
    def invalidate_all(self, user_id: str, purpose: str) -> None:
        """Invalidate all pending OTPs for a user and purpose."""
        pass
