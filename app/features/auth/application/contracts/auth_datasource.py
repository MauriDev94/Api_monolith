from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.features.users.domain.entities.user import User

if TYPE_CHECKING:
    from app.features.auth.application.dto.register_user_params import RegisterUserParams


class AuthDatasource(ABC):
    """Application port for authentication-related persistence operations."""

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> User | None:
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    def register_user(self, params: RegisterUserParams, password_hash: str) -> User:
        pass
