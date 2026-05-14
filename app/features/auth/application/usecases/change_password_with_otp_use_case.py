from app.common.use_case import UseCase
from app.core.exceptions.exceptions import NotFoundError, UnauthorizedError
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.otp_datasource import OtpDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.dto.change_password_with_otp_params import (
    ChangePasswordWithOtpParams,
)
from app.features.auth.domain.value_objects.otp_purpose import OtpPurpose


class ChangePasswordWithOtpUseCase(UseCase[ChangePasswordWithOtpParams, None]):
    """Change user password after validating a one-time code."""

    def __init__(
        self,
        auth_datasource: AuthDatasource,
        otp_datasource: OtpDatasource,
        password_manager: PasswordManager,
        token_revocation_store: TokenRevocationStore,
    ):
        self.auth_datasource = auth_datasource
        self.otp_datasource = otp_datasource
        self.password_manager = password_manager
        self.token_revocation_store = token_revocation_store

    def execute(self, params: ChangePasswordWithOtpParams) -> None:
        user = self.auth_datasource.get_user_by_id(params.user_id)
        if user is None:
            raise NotFoundError("user not found")

        otp = self.otp_datasource.find_valid(
            user_id=params.user_id,
            code=params.code,
            purpose=OtpPurpose.PASSWORD_CHANGE,
        )
        if otp is None:
            raise UnauthorizedError("Invalid otp code")

        otp.consume()
        self.otp_datasource.save(otp)

        password_hash = self.password_manager.hash_password(params.new_password)
        self.auth_datasource.update_password(user_id=params.user_id, password_hash=password_hash)
        self.token_revocation_store.revoke_all_for_user(params.user_id)
        return None
