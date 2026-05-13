"""Google OAuth2 provider implementation using httpx."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx

from app.core.config.env_config import EnvConfig
from app.features.auth.application.contracts.oauth_provider import (
    GoogleTokenData,
    GoogleUserInfo,
    OAuthProvider,
)

if TYPE_CHECKING:
    pass


class GoogleOAuthProviderImpl(OAuthProvider):
    """Implementation of OAuthProvider for Google OAuth2."""

    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self, config: EnvConfig) -> None:
        self._config = config
        self._client_id = config.google_client_id
        self._client_secret = config.google_client_secret
        self._redirect_uri = config.google_redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """Build the Google OAuth2 authorization URL."""
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> GoogleTokenData:
        """Exchange authorization code for tokens."""
        data = {
            "code": code,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": self._redirect_uri,
            "grant_type": "authorization_code",
        }

        with httpx.Client() as client:
            response = client.post(self.TOKEN_URL, data=data, timeout=30.0)
            response.raise_for_status()
            token_response = response.json()

        return GoogleTokenData(
            access_token=token_response["access_token"],
            id_token=token_response["id_token"],
        )

    def get_user_info(self, access_token: str, id_token: str) -> GoogleUserInfo:
        """Fetch user info from Google."""
        headers = {"Authorization": f"Bearer {access_token}"}

        with httpx.Client() as client:
            response = client.get(self.USER_INFO_URL, headers=headers, timeout=30.0)
            response.raise_for_status()
            user_data = response.json()

        # Prefer structured fields from Google and fallback to full name parsing
        full_name = user_data.get("name", "")
        given_name = user_data.get("given_name") or (
            full_name.split(" ", 1)[0] if full_name else ""
        )
        family_name = user_data.get("family_name") or (
            full_name.split(" ", 1)[1] if " " in full_name else ""
        )

        return GoogleUserInfo(
            google_id=user_data["sub"],
            email=user_data["email"],
            name=given_name,
            lastname=family_name,
            email_verified=user_data.get("email_verified", False),
        )
