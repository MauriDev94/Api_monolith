"""Initiate Google OAuth login."""

from __future__ import annotations

from dataclasses import dataclass

from app.common.use_case import UseCase
from app.features.auth.application.contracts.oauth_provider import OAuthProvider


@dataclass(frozen=True, slots=True)
class InitiateGoogleLoginParams:
    """Params for initiating Google login."""

    pass


@dataclass(frozen=True, slots=True)
class InitiateGoogleLoginResult:
    """Result with authorization URL and state."""

    authorization_url: str
    state: str


class InitiateGoogleLoginUseCase(UseCase[InitiateGoogleLoginParams, InitiateGoogleLoginResult]):
    """Generate Google OAuth authorization URL and state."""

    def __init__(self, oauth_provider: OAuthProvider) -> None:
        self._oauth_provider = oauth_provider

    def execute(self, params: InitiateGoogleLoginParams) -> InitiateGoogleLoginResult:
        state = self._generate_state()
        authorization_url = self._oauth_provider.get_authorization_url(state)
        return InitiateGoogleLoginResult(authorization_url=authorization_url, state=state)

    def _generate_state(self) -> str:
        import secrets

        return secrets.token_urlsafe(32)
