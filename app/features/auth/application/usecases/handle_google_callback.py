"""Handle Google OAuth callback and issue tokens."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC

from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ConflictError, UnauthorizedError
from app.features.auth.application.contracts.google_auth_datasource import GoogleAuthDatasource
from app.features.auth.application.contracts.oauth_provider import OAuthProvider
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.dto.create_google_user_params import CreateGoogleUserParams
from app.features.auth.application.dto.token_pair_result import TokenPairResult
from app.features.auth.domain.value_objects.refresh_token_id import RefreshTokenId


@dataclass(frozen=True, slots=True)
class HandleGoogleCallbackParams:
    """Params for Google OAuth callback."""

    code: str
    state: str | None = None


class HandleGoogleCallbackUseCase(UseCase[HandleGoogleCallbackParams, TokenPairResult]):
    """Handle Google OAuth callback: exchange code, find/create user, issue tokens."""

    def __init__(
        self,
        oauth_provider: OAuthProvider,
        google_auth_datasource: GoogleAuthDatasource,
        token_manager: TokenManager,
        token_revocation_store: TokenRevocationStore,
    ) -> None:
        self._oauth_provider = oauth_provider
        self._google_auth_datasource = google_auth_datasource
        self._token_manager = token_manager
        self._token_revocation_store = token_revocation_store

    def execute(self, params: HandleGoogleCallbackParams) -> TokenPairResult:
        # Exchange code for tokens
        token_data = self._oauth_provider.exchange_code(params.code)

        # Get user info from Google
        user_info = self._oauth_provider.get_user_info(
            access_token=token_data.access_token,
            id_token=token_data.id_token,
        )

        # Try to find user by google_id
        user = self._google_auth_datasource.get_user_by_google_id(user_info.google_id)
        if user:
            return self._issue_tokens(user.id)

        # Try to find user by email
        user = self._google_auth_datasource.get_user_by_email(user_info.email)

        if user:
            # User exists with email
            if user.password_hash is not None:
                # Password account without Google - conflict
                raise ConflictError(
                    "This email already has a password account. "
                    "Please link your Google account in Settings."
                )
            # Social-only user (no password) - link and login
            if user.id:
                self._google_auth_datasource.link_google_id(user.id, user_info.google_id)
            return self._issue_tokens(user.id)

        # New user - create account
        create_params = CreateGoogleUserParams(
            google_id=user_info.google_id,
            email=user_info.email,
            name=user_info.name,
            lastname=user_info.lastname,
            google_email_verified=user_info.email_verified,
        )
        new_user = self._google_auth_datasource.create_google_user(create_params)
        return self._issue_tokens(new_user.id)

    def _issue_tokens(self, user_id: str | None) -> TokenPairResult:
        if user_id is None:
            raise UnauthorizedError("User ID is missing")

        access_token = self._token_manager.create_access_token(subject=user_id)
        refresh_token_id = RefreshTokenId.generate()
        refresh_token = self._token_manager.create_refresh_token(
            subject=user_id,
            claims={"jti": refresh_token_id.value},
        )

        # Store refresh token for revocation tracking
        from datetime import datetime

        payload = self._token_manager.decode_refresh_token(refresh_token)
        expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
        self._token_revocation_store.store_active(
            jti=refresh_token_id.value,
            user_id=user_id,
            expires_at=expires_at,
        )

        return TokenPairResult(access_token=access_token, refresh_token=refresh_token)
