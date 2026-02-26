from abc import ABC, abstractmethod
from typing import Any


class TokenManager(ABC):
    """Application port for JWT access and refresh token lifecycle."""

    @abstractmethod
    def create_access_token(self, subject: str, claims: dict[str, Any] | None = None) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, subject: str, claims: dict[str, Any] | None = None) -> str:
        pass

    @abstractmethod
    def decode_access_token(self, token: str) -> dict[str, Any]:
        pass

    @abstractmethod
    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        pass
