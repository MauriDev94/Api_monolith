from app.common.use_case import UseCase
from app.core.exceptions.exceptions import InvalidCredentialsException
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.dto.login_user_params import LoginUserParams
from app.features.auth.application.dto.token_pair_result import TokenPairResult
from app.features.users.domain.value_objects.email import Email


class LoginUser(UseCase[LoginUserParams, TokenPairResult]):
    """Authenticate user credentials and issue token pair."""

    def __init__(
        self,
        auth_datasource: AuthDatasource,
        password_manager: PasswordManager,
        token_manager: TokenManager,
    ):
        self.auth_datasource = auth_datasource
        self.password_manager = password_manager
        self.token_manager = token_manager

    def execute(self, params: LoginUserParams) -> TokenPairResult:
        normalized_email = Email(params.email).value

        user = self.auth_datasource.get_user_by_email(normalized_email)
        if user is None:
            raise InvalidCredentialsException()

        is_valid_password = self.password_manager.verify_password(
            params.password,
            user.password_hash,
        )
        if not is_valid_password:
            raise InvalidCredentialsException()

        subject = user.id or ""
        access_token = self.token_manager.create_access_token(subject=subject)
        refresh_token = self.token_manager.create_refresh_token(subject=subject)
        return TokenPairResult(access_token=access_token, refresh_token=refresh_token)
