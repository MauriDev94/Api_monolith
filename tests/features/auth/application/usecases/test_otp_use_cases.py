from datetime import date
from unittest.mock import Mock

import pytest

from app.core.exceptions.exceptions import NotFoundError, UnauthorizedError
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.email_sender import EmailSender
from app.features.auth.application.contracts.otp_datasource import OtpDatasource
from app.features.auth.application.dto.request_otp_params import RequestOtpParams
from app.features.auth.application.dto.verify_otp_params import VerifyOtpParams
from app.features.auth.application.usecases.request_otp_use_case import RequestOtpUseCase
from app.features.auth.application.usecases.verify_otp_use_case import VerifyOtpUseCase
from app.features.auth.domain.entities.otp_code import OtpCode
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
    return OtpCode.create(user_id="user-1", purpose="login")


# Tipo de test: Unit
def test_should_raise_not_found_when_requesting_otp_for_missing_user() -> None:
    auth_datasource = Mock(spec=AuthDatasource)
    otp_datasource = Mock(spec=OtpDatasource)
    email_sender = Mock(spec=EmailSender)
    auth_datasource.get_user_by_id.return_value = None
    use_case = RequestOtpUseCase(auth_datasource, otp_datasource, email_sender)

    with pytest.raises(NotFoundError, match="user not found"):
        use_case.execute(RequestOtpParams(user_id="missing", purpose="login"))

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

    use_case.execute(RequestOtpParams(user_id="user-1", purpose="login"))

    otp_datasource.invalidate_all.assert_called_once_with("user-1", "login")
    otp_datasource.save.assert_called_once()
    email_sender.send_otp.assert_called_once_with(
        to_email="mauri@mail.com",
        code=otp.code,
        purpose="login",
    )


# Tipo de test: Unit
def test_should_raise_unauthorized_when_otp_is_invalid() -> None:
    otp_datasource = Mock(spec=OtpDatasource)
    otp_datasource.find_valid.return_value = None
    use_case = VerifyOtpUseCase(otp_datasource)

    with pytest.raises(UnauthorizedError, match="Invalid otp code"):
        use_case.execute(VerifyOtpParams(user_id="user-1", code="123456", purpose="login"))

    otp_datasource.save.assert_not_called()


# Tipo de test: Unit
def test_should_consume_and_persist_valid_otp() -> None:
    otp_datasource = Mock(spec=OtpDatasource)
    otp = make_otp()
    otp_datasource.find_valid.return_value = otp
    use_case = VerifyOtpUseCase(otp_datasource)

    use_case.execute(VerifyOtpParams(user_id="user-1", code=otp.code, purpose="login"))

    assert otp.used_at is not None
    otp_datasource.save.assert_called_once_with(otp)
