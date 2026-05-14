from datetime import date
from unittest.mock import Mock

import pytest

from app.core.exceptions.exceptions import NotFoundError, UnauthorizedError
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.otp_datasource import OtpDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.dto.change_password_with_otp_params import (
    ChangePasswordWithOtpParams,
)
from app.features.auth.application.usecases.change_password_with_otp_use_case import (
    ChangePasswordWithOtpUseCase,
)
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


def make_params() -> ChangePasswordWithOtpParams:
    return ChangePasswordWithOtpParams(
        user_id="user-1",
        code="123456",
        new_password="new-password-123",
    )


# Tipo de test: Unit
def test_should_raise_not_found_when_user_does_not_exist() -> None:
    auth_datasource = Mock(spec=AuthDatasource)
    otp_datasource = Mock(spec=OtpDatasource)
    password_manager = Mock(spec=PasswordManager)
    token_revocation_store = Mock(spec=TokenRevocationStore)
    auth_datasource.get_user_by_id.return_value = None
    use_case = ChangePasswordWithOtpUseCase(
        auth_datasource=auth_datasource,
        otp_datasource=otp_datasource,
        password_manager=password_manager,
        token_revocation_store=token_revocation_store,
    )

    with pytest.raises(NotFoundError, match="user not found"):
        use_case.execute(make_params())

    otp_datasource.find_valid.assert_not_called()
    auth_datasource.update_password.assert_not_called()
    token_revocation_store.revoke_all_for_user.assert_not_called()


# Tipo de test: Unit
def test_should_raise_unauthorized_when_otp_is_invalid() -> None:
    auth_datasource = Mock(spec=AuthDatasource)
    otp_datasource = Mock(spec=OtpDatasource)
    password_manager = Mock(spec=PasswordManager)
    token_revocation_store = Mock(spec=TokenRevocationStore)
    auth_datasource.get_user_by_id.return_value = make_user()
    otp_datasource.find_valid.return_value = None
    use_case = ChangePasswordWithOtpUseCase(
        auth_datasource=auth_datasource,
        otp_datasource=otp_datasource,
        password_manager=password_manager,
        token_revocation_store=token_revocation_store,
    )

    with pytest.raises(UnauthorizedError, match="Invalid otp code"):
        use_case.execute(make_params())

    otp_datasource.find_valid.assert_called_once_with(
        user_id="user-1",
        code="123456",
        purpose=OtpPurpose.PASSWORD_CHANGE,
    )
    password_manager.hash_password.assert_not_called()
    auth_datasource.update_password.assert_not_called()
    token_revocation_store.revoke_all_for_user.assert_not_called()


# Tipo de test: Unit
def test_should_change_password_and_revoke_tokens_when_otp_is_valid() -> None:
    auth_datasource = Mock(spec=AuthDatasource)
    otp_datasource = Mock(spec=OtpDatasource)
    password_manager = Mock(spec=PasswordManager)
    token_revocation_store = Mock(spec=TokenRevocationStore)
    auth_datasource.get_user_by_id.return_value = make_user()
    otp = OtpCode.create(user_id="user-1", purpose=OtpPurpose.PASSWORD_CHANGE)
    otp_datasource.find_valid.return_value = otp
    password_manager.hash_password.return_value = "hashed-new-password"
    use_case = ChangePasswordWithOtpUseCase(
        auth_datasource=auth_datasource,
        otp_datasource=otp_datasource,
        password_manager=password_manager,
        token_revocation_store=token_revocation_store,
    )

    use_case.execute(make_params())

    assert otp.used_at is not None
    otp_datasource.save.assert_called_once_with(otp)
    password_manager.hash_password.assert_called_once_with("new-password-123")
    auth_datasource.update_password.assert_called_once_with(
        user_id="user-1",
        password_hash="hashed-new-password",
    )
    token_revocation_store.revoke_all_for_user.assert_called_once_with("user-1")


# Tipo de test: Unit
def test_should_not_revoke_tokens_when_password_update_fails() -> None:
    auth_datasource = Mock(spec=AuthDatasource)
    otp_datasource = Mock(spec=OtpDatasource)
    password_manager = Mock(spec=PasswordManager)
    token_revocation_store = Mock(spec=TokenRevocationStore)
    auth_datasource.get_user_by_id.return_value = make_user()
    otp_datasource.find_valid.return_value = OtpCode.create(
        user_id="user-1",
        purpose=OtpPurpose.PASSWORD_CHANGE,
    )
    password_manager.hash_password.return_value = "hashed-new-password"
    auth_datasource.update_password.side_effect = RuntimeError("db write failed")
    use_case = ChangePasswordWithOtpUseCase(
        auth_datasource=auth_datasource,
        otp_datasource=otp_datasource,
        password_manager=password_manager,
        token_revocation_store=token_revocation_store,
    )

    with pytest.raises(RuntimeError, match="db write failed"):
        use_case.execute(make_params())

    token_revocation_store.revoke_all_for_user.assert_not_called()
