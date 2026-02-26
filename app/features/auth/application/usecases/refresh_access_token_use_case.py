from app.common.use_case import UseCase
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.dto.refresh_token_params import RefreshTokenParams
from app.features.auth.application.dto.token_pair_result import TokenPairResult


class RefreshAccessToken(UseCase[RefreshTokenParams, TokenPairResult]):
    """Issue a new access token from a valid refresh token."""

    def __init__(self, token_manager: TokenManager):
        self.token_manager = token_manager

    def execute(self, params: RefreshTokenParams) -> TokenPairResult:
        payload = self.token_manager.decode_refresh_token(params.refresh_token)
        subject = str(payload.get("sub", ""))
        if not subject:
            raise ValueError("invalid token")

        access_token = self.token_manager.create_access_token(subject=subject)
        return TokenPairResult(
            access_token=access_token,
            refresh_token=params.refresh_token,
        )
