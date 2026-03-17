from app.common.use_case import UseCase
from app.core.exceptions.exceptions import NotFoundError
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.email_sender import EmailSender
from app.features.auth.application.contracts.otp_datasource import OtpDatasource
from app.features.auth.application.dto.request_otp_params import RequestOtpParams
from app.features.auth.domain.entities.otp_code import OtpCode


class RequestOtpUseCase(UseCase[RequestOtpParams, None]):
    """Generate and deliver a one-time password for a user."""

    def __init__(
        self,
        auth_datasource: AuthDatasource,
        otp_datasource: OtpDatasource,
        email_sender: EmailSender,
    ):
        self.auth_datasource = auth_datasource
        self.otp_datasource = otp_datasource
        self.email_sender = email_sender

    def execute(self, params: RequestOtpParams) -> None:
        user = self.auth_datasource.get_user_by_id(params.user_id)
        if user is None:
            raise NotFoundError("user not found")

        self.otp_datasource.invalidate_all(params.user_id, params.purpose)
        otp = OtpCode.create(user_id=params.user_id, purpose=params.purpose)
        persisted = self.otp_datasource.save(otp)
        self.email_sender.send_otp(
            to_email=user.email.value,
            code=persisted.code,
            purpose=persisted.purpose,
        )
        return None
