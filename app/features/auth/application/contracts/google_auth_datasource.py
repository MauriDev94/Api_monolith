"""Google Auth datasource contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.features.users.domain.entities.user import User

if TYPE_CHECKING:
    from app.features.auth.application.dto.create_google_user_params import CreateGoogleUserParams


class GoogleAuthDatasource(ABC):
    """Application port for Google OAuth-related persistence operations."""

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> User | None:
        """Find user by their ID."""

    @abstractmethod
    def get_user_by_google_id(self, google_id: str) -> User | None:
        """Find user by their Google ID."""

    @abstractmethod
    def get_user_by_email(self, email: str) -> User | None:
        """Find user by email address."""

    @abstractmethod
    def create_google_user(self, params: CreateGoogleUserParams) -> User:
        """Create a new user from Google OAuth data."""

    @abstractmethod
    def link_google_id(self, user_id: str, google_id: str) -> None:
        """Link a Google ID to an existing user."""
