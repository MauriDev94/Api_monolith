"""Stub Google OAuth provider for testing."""

from __future__ import annotations

from dataclasses import dataclass

from app.features.auth.application.contracts.oauth_provider import (
    GoogleTokenData,
    GoogleUserInfo,
    OAuthProvider,
)


@dataclass(frozen=True, slots=True)
class StubGoogleOAuthUser:
    """Stub user data for testing."""

    google_id: str
    email: str
    name: str
    lastname: str
    email_verified: bool = True


class StubGoogleOAuthProvider(OAuthProvider):
    """Stub implementation of OAuthProvider for testing without real Google."""

    def __init__(self, stub_user: StubGoogleOAuthUser | None = None) -> None:
        self._stub_user = stub_user or StubGoogleOAuthUser(
            google_id="stub-google-id-123",
            email="testuser@gmail.com",
            name="Test",
            lastname="User",
            email_verified=True,
        )
        self._last_authorization_url: str | None = None
        self._last_code: str | None = None

    def get_authorization_url(self, state: str) -> str:
        """Return a fake authorization URL."""
        self._last_authorization_url = f"https://accounts.google.com/oauth2/fake?state={state}"
        return self._last_authorization_url

    def exchange_code(self, code: str) -> GoogleTokenData:
        """Return fake tokens for any code."""
        self._last_code = code
        return GoogleTokenData(
            access_token="stub-access-token-123",
            id_token="stub-id-token-456",
        )

    def get_user_info(self, access_token: str, id_token: str) -> GoogleUserInfo:
        """Return stub user info."""
        return GoogleUserInfo(
            google_id=self._stub_user.google_id,
            email=self._stub_user.email,
            name=self._stub_user.name,
            lastname=self._stub_user.lastname,
            email_verified=self._stub_user.email_verified,
        )

    @property
    def last_authorization_url(self) -> str | None:
        """Get the last authorization URL generated."""
        return self._last_authorization_url

    @property
    def last_code(self) -> str | None:
        """Get the last code passed to exchange_code."""
        return self._last_code
