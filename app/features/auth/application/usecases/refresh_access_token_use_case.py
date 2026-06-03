from datetime import UTC, datetime

from app.common.use_case import UseCase
from app.core.exceptions.exceptions import UnauthorizedError
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.dto.refresh_token_params import RefreshTokenParams
from app.features.auth.application.dto.token_pair_result import TokenPairResult
from app.features.auth.domain.value_objects.refresh_token_id import RefreshTokenId


class RefreshAccessToken(UseCase[RefreshTokenParams, TokenPairResult]):
    """Issue a new access token from a valid refresh token."""

    def __init__(self, token_manager: TokenManager, token_revocation_store: TokenRevocationStore):
        self.token_manager = token_manager
        self.token_revocation_store = token_revocation_store

    def execute(self, params: RefreshTokenParams) -> TokenPairResult:
        payload = self.token_manager.decode_refresh_token(params.refresh_token)
        subject = str(payload.get("sub", ""))
        jti = str(payload.get("jti", ""))
        if not subject or not jti:
            raise UnauthorizedError()

        if self.token_revocation_store.is_revoked(jti):
            self.token_revocation_store.revoke_all_for_user(subject)
            raise UnauthorizedError()

        self.token_revocation_store.revoke(jti)
        access_token = self.token_manager.create_access_token(subject=subject)
        refresh_token_id = RefreshTokenId.generate()
        refresh_token = self.token_manager.create_refresh_token(
            subject=subject,
            claims={"jti": refresh_token_id.value},
        )
        new_payload = self.token_manager.decode_refresh_token(refresh_token)
        expires_at = datetime.fromtimestamp(new_payload["exp"], tz=UTC)
        self.token_revocation_store.store_active(
            jti=refresh_token_id.value,
            user_id=subject,
            expires_at=expires_at,
        )
        return TokenPairResult(
            access_token=access_token,
            refresh_token=refresh_token,
        )
