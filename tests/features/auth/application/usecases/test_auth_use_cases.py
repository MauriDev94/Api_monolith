from datetime import date
from unittest.mock import Mock

import pytest

from app.core.exceptions.exceptions import InvalidCredentialsException, ResourceConflictException
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.dto.login_user_params import LoginUserParams
from app.features.auth.application.dto.refresh_token_params import RefreshTokenParams
from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.auth.application.usecases.get_current_user_use_case import GetCurrentUser
from app.features.auth.application.usecases.login_user_use_case import LoginUser
from app.features.auth.application.usecases.refresh_access_token_use_case import RefreshAccessToken
from app.features.auth.application.usecases.register_user_use_case import RegisterUser
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


# Tipo de test: Unit
def test_should_raise_conflict_when_registering_existing_email() -> None:
    """Valida que lanza conflicto cuando registrar existente email."""
    datasource = Mock(spec=AuthDatasource)
    password_manager = Mock(spec=PasswordManager)
    datasource.get_user_by_email.return_value = make_user()
    use_case = RegisterUser(auth_datasource=datasource, password_manager=password_manager)
    params = RegisterUserParams(
        name="Mauri",
        lastname="Salinas",
        email="mauri@mail.com",
        password="plain1234",
        birthdate=date(2000, 1, 1),
    )

    with pytest.raises(ResourceConflictException, match="email already registered"):
        use_case.execute(params)


# Tipo de test: Unit
def test_should_hash_password_and_register_new_user() -> None:
    """Valida que hash contrasena y registrar new usuario."""
    datasource = Mock(spec=AuthDatasource)
    password_manager = Mock(spec=PasswordManager)
    datasource.get_user_by_email.return_value = None
    password_manager.hash_password.return_value = "hashed-password"
    datasource.register_user.return_value = make_user()
    use_case = RegisterUser(auth_datasource=datasource, password_manager=password_manager)
    params = RegisterUserParams(
        name="Mauri",
        lastname="Salinas",
        email="mauri@mail.com",
        password="plain1234",
        birthdate=date(2000, 1, 1),
    )

    result = use_case.execute(params)

    password_manager.hash_password.assert_called_once_with("plain1234")
    datasource.register_user.assert_called_once_with(params=params, password_hash="hashed-password")
    assert result.id == "user-1"


# Tipo de test: Unit
def test_should_raise_invalid_credentials_when_login_user_not_found() -> None:
    """Valida que lanza invalido credenciales cuando login usuario no encontrado."""
    datasource = Mock(spec=AuthDatasource)
    password_manager = Mock(spec=PasswordManager)
    token_manager = Mock(spec=TokenManager)
    datasource.get_user_by_email.return_value = None
    use_case = LoginUser(datasource, password_manager, token_manager)

    with pytest.raises(InvalidCredentialsException):
        use_case.execute(LoginUserParams(email="x@mail.com", password="bad"))


# Tipo de test: Unit
def test_should_raise_invalid_credentials_when_login_password_is_invalid() -> None:
    """Valida que lanza invalido credenciales cuando login contrasena es invalido."""
    datasource = Mock(spec=AuthDatasource)
    password_manager = Mock(spec=PasswordManager)
    token_manager = Mock(spec=TokenManager)
    datasource.get_user_by_email.return_value = make_user()
    password_manager.verify_password.return_value = False
    use_case = LoginUser(datasource, password_manager, token_manager)

    with pytest.raises(InvalidCredentialsException):
        use_case.execute(LoginUserParams(email="mauri@mail.com", password="bad"))


# Tipo de test: Unit
def test_should_return_token_pair_when_login_is_valid() -> None:
    """Valida que retorna token pair cuando login es valido."""
    datasource = Mock(spec=AuthDatasource)
    password_manager = Mock(spec=PasswordManager)
    token_manager = Mock(spec=TokenManager)
    datasource.get_user_by_email.return_value = make_user()
    password_manager.verify_password.return_value = True
    token_manager.create_access_token.return_value = "access-token"
    token_manager.create_refresh_token.return_value = "refresh-token"
    use_case = LoginUser(datasource, password_manager, token_manager)

    result = use_case.execute(LoginUserParams(email="mauri@mail.com", password="ok"))

    token_manager.create_access_token.assert_called_once_with(subject="user-1")
    token_manager.create_refresh_token.assert_called_once_with(subject="user-1")
    assert result.access_token == "access-token"
    assert result.refresh_token == "refresh-token"


# Tipo de test: Unit
def test_should_raise_invalid_credentials_when_refresh_subject_is_missing() -> None:
    """Valida que lanza invalido credenciales cuando refresh subject es faltante."""
    token_manager = Mock(spec=TokenManager)
    token_manager.decode_refresh_token.return_value = {"sub": ""}
    use_case = RefreshAccessToken(token_manager)

    with pytest.raises(InvalidCredentialsException):
        use_case.execute(RefreshTokenParams(refresh_token="invalid"))


# Tipo de test: Unit
def test_should_return_new_access_token_when_refresh_is_valid() -> None:
    """Valida que retorna new acceso token cuando refresh es valido."""
    token_manager = Mock(spec=TokenManager)
    token_manager.decode_refresh_token.return_value = {"sub": "user-1"}
    token_manager.create_access_token.return_value = "new-access"
    use_case = RefreshAccessToken(token_manager)

    result = use_case.execute(RefreshTokenParams(refresh_token="refresh"))

    token_manager.create_access_token.assert_called_once_with(subject="user-1")
    assert result.access_token == "new-access"
    assert result.refresh_token == "refresh"


# Tipo de test: Unit
def test_should_raise_invalid_credentials_when_access_token_subject_is_missing() -> None:
    """Valida que lanza invalido credenciales cuando acceso token subject es faltante."""
    datasource = Mock(spec=AuthDatasource)
    token_manager = Mock(spec=TokenManager)
    token_manager.decode_access_token.return_value = {"sub": ""}
    use_case = GetCurrentUser(datasource, token_manager)

    with pytest.raises(InvalidCredentialsException):
        use_case.execute("token")


# Tipo de test: Unit
def test_should_raise_invalid_credentials_when_current_user_not_found() -> None:
    """Valida que lanza invalido credenciales cuando actual usuario no encontrado."""
    datasource = Mock(spec=AuthDatasource)
    token_manager = Mock(spec=TokenManager)
    token_manager.decode_access_token.return_value = {"sub": "user-1"}
    datasource.get_user_by_id.return_value = None
    use_case = GetCurrentUser(datasource, token_manager)

    with pytest.raises(InvalidCredentialsException):
        use_case.execute("token")


# Tipo de test: Unit
def test_should_return_current_user_when_access_token_is_valid() -> None:
    """Valida que retorna actual usuario cuando acceso token es valido."""
    datasource = Mock(spec=AuthDatasource)
    token_manager = Mock(spec=TokenManager)
    expected_user = make_user()
    token_manager.decode_access_token.return_value = {"sub": "user-1"}
    datasource.get_user_by_id.return_value = expected_user
    use_case = GetCurrentUser(datasource, token_manager)

    result = use_case.execute("token")

    datasource.get_user_by_id.assert_called_once_with("user-1")
    assert result == expected_user
