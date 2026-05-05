"""OAuth Provider contract for external identity providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GoogleUserInfo:
    """User info returned from Google OAuth2."""

    google_id: str
    email: str
    name: str
    lastname: str
    email_verified: bool


@dataclass(frozen=True, slots=True)
class GoogleTokenData:
    """Token data from Google OAuth2 code exchange."""

    access_token: str
    id_token: str


class OAuthProvider(ABC):
    """Abstract contract for OAuth2 providers."""

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Build the authorization URL to redirect the user."""

    @abstractmethod
    def exchange_code(self, code: str) -> GoogleTokenData:
        """Exchange authorization code for tokens."""

    @abstractmethod
    def get_user_info(self, access_token: str, id_token: str) -> GoogleUserInfo:
        """Fetch user info from the provider."""
