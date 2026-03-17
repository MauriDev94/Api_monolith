from app.common.use_case import UseCase
from app.core.exceptions.exceptions import UnauthorizedError
from app.features.auth.application.contracts.otp_datasource import OtpDatasource
from app.features.auth.application.dto.verify_otp_params import VerifyOtpParams


class VerifyOtpUseCase(UseCase[VerifyOtpParams, None]):
    """Validate a one-time password and consume it."""

    def __init__(self, otp_datasource: OtpDatasource):
        self.otp_datasource = otp_datasource

    def execute(self, params: VerifyOtpParams) -> None:
        otp = self.otp_datasource.find_valid(
            user_id=params.user_id,
            code=params.code,
            purpose=params.purpose,
        )
        if otp is None:
            raise UnauthorizedError("Invalid otp code")

        otp.consume()
        self.otp_datasource.save(otp)
        return None
