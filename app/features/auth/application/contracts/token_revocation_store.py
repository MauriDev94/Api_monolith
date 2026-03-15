from abc import ABC, abstractmethod
from datetime import datetime


class TokenRevocationStore(ABC):
    """Application port for refresh token revocation and rotation tracking."""

    @abstractmethod
    def store_active(self, jti: str, user_id: str, expires_at: datetime) -> None:
        """Persist an active refresh token identifier until expiration."""
        pass

    @abstractmethod
    def revoke(self, jti: str) -> None:
        """Mark a refresh token identifier as revoked."""
        pass

    @abstractmethod
    def is_revoked(self, jti: str) -> bool:
        """Return True when the refresh token identifier is revoked or unknown."""
        pass

    @abstractmethod
    def revoke_all_for_user(self, user_id: str) -> None:
        """Revoke all active refresh tokens for the user."""
        pass
