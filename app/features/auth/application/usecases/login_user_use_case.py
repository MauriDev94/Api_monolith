from datetime import datetime, timezone

from app.common.use_case import UseCase
from app.core.exceptions.exceptions import InternalServerError, UnauthorizedError
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.dto.login_user_params import LoginUserParams
from app.features.auth.application.dto.token_pair_result import TokenPairResult
from app.features.auth.domain.value_objects.refresh_token_id import RefreshTokenId
from app.features.users.domain.value_objects.email import Email


class LoginUser(UseCase[LoginUserParams, TokenPairResult]):
    """Authenticate user credentials and issue token pair."""

    def __init__(
        self,
        auth_datasource: AuthDatasource,
        password_manager: PasswordManager,
        token_manager: TokenManager,
        token_revocation_store: TokenRevocationStore,
    ):
        self.auth_datasource = auth_datasource
        self.password_manager = password_manager
        self.token_manager = token_manager
        self.token_revocation_store = token_revocation_store

    def execute(self, params: LoginUserParams) -> TokenPairResult:
        try:
            normalized_email = Email(params.email).value
        except ValueError as exc:
            # Keep authentication response stable and avoid leaking format details.
            raise UnauthorizedError("Invalid email or password") from exc

        user = self.auth_datasource.get_user_by_email(normalized_email)
        if user is None:
            raise UnauthorizedError("Invalid email or password")

        is_valid_password = self.password_manager.verify_password(
            params.password,
            user.password_hash,
        )
        if not is_valid_password:
            raise UnauthorizedError("Invalid email or password")

        if user.id is None:
            raise InternalServerError("authenticated user id is missing")

        subject = user.id
        access_token = self.token_manager.create_access_token(subject=subject)
        refresh_token_id = RefreshTokenId.generate()
        refresh_token = self.token_manager.create_refresh_token(
            subject=subject,
            claims={"jti": refresh_token_id.value},
        )
        payload = self.token_manager.decode_refresh_token(refresh_token)
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        self.token_revocation_store.store_active(
            jti=refresh_token_id.value,
            user_id=subject,
            expires_at=expires_at,
        )
        return TokenPairResult(access_token=access_token, refresh_token=refresh_token)
