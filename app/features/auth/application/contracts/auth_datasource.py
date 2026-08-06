from __future__ import annotations

from abc import ABC, abstractmethod

from app.features.users.domain.entities.user import User


class AuthDatasource(ABC):
    """Application port for authentication-related persistence operations."""

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> User | None:
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    def register_user(self, user: User) -> User:
        """Persist a user entity already built and validated by the domain."""
        pass

    @abstractmethod
    def update_password(self, user_id: str, password_hash: str) -> None:
        """Persist a new password hash for an existing user."""
        pass
