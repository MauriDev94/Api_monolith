from datetime import date
from unittest.mock import Mock

import pytest

from app.core.exceptions.exceptions import NotFoundError
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.email_sender import EmailSender
from app.features.auth.application.contracts.otp_datasource import OtpDatasource
from app.features.auth.application.dto.request_otp_params import RequestOtpParams
from app.features.auth.application.usecases.request_otp_use_case import RequestOtpUseCase
from app.features.auth.domain.entities.otp_code import OtpCode
from app.features.auth.domain.value_objects.otp_purpose import OtpPurpose
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


def make_user() -> User:
    return User(
        id="user-1",
        name="Mauri",
        lastname="Salinas",
        email=Email("mauri@mail.com"),
        password_hash="hashed-password",
        birthdate=date(2000, 1, 1),
    )


def make_otp() -> OtpCode:
    return OtpCode.create(user_id="user-1", purpose=OtpPurpose.PASSWORD_CHANGE)


# Tipo de test: Unit
def test_should_raise_not_found_when_requesting_otp_for_missing_user() -> None:
    auth_datasource = Mock(spec=AuthDatasource)
    otp_datasource = Mock(spec=OtpDatasource)
    email_sender = Mock(spec=EmailSender)
    auth_datasource.get_user_by_id.return_value = None
    use_case = RequestOtpUseCase(auth_datasource, otp_datasource, email_sender)

    with pytest.raises(NotFoundError, match="user not found"):
        use_case.execute(RequestOtpParams(user_id="missing", purpose=OtpPurpose.PASSWORD_CHANGE))

    otp_datasource.invalidate_all.assert_not_called()
    otp_datasource.save.assert_not_called()
    email_sender.send_otp.assert_not_called()


# Tipo de test: Unit
def test_should_invalidate_previous_otps_and_send_new_one() -> None:
    auth_datasource = Mock(spec=AuthDatasource)
    otp_datasource = Mock(spec=OtpDatasource)
    email_sender = Mock(spec=EmailSender)
    user = make_user()
    auth_datasource.get_user_by_id.return_value = user
    otp = make_otp()
    otp_datasource.save.return_value = otp
    use_case = RequestOtpUseCase(auth_datasource, otp_datasource, email_sender)

    use_case.execute(RequestOtpParams(user_id="user-1", purpose=OtpPurpose.PASSWORD_CHANGE))

    otp_datasource.invalidate_all.assert_called_once_with("user-1", OtpPurpose.PASSWORD_CHANGE)
    otp_datasource.save.assert_called_once()
    email_sender.send_otp.assert_called_once_with(
        to_email="mauri@mail.com",
        code=otp.code,
        purpose=OtpPurpose.PASSWORD_CHANGE,
    )
