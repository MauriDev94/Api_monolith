from datetime import date
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions.error_handling import register_exception_handlers
from app.core.exceptions.exceptions import InvalidCredentialsException
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.usecases.login_user_use_case import LoginUser
from app.features.auth.di.dependencies import get_login_user_use_case, get_register_user_use_case
from app.features.auth.presentation.api import v1_router
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


class StubUseCase:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.received = None

    def execute(self, params=None):
        self.received = params
        if self.error is not None:
            raise self.error
        return self.result


def make_user() -> User:
    return User(
        id="user-1",
        name="Mauri",
        lastname="Salinas",
        email=Email("mauri@mail.com"),
        password_hash="hashed-password",
        birthdate=date(2000, 1, 1),
    )


def create_test_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(v1_router, prefix="/auth")
    return TestClient(app, raise_server_exceptions=False)


# Tipo de test: Integration
def test_should_return_400_when_register_email_violates_domain_policy() -> None:
    """Valida que register retorna 400 si el email pasa EmailStr pero falla la policy del VO."""
    client = create_test_client()
    register_use_case = StubUseCase(result=make_user())
    client.app.dependency_overrides[get_register_user_use_case] = lambda: register_use_case

    response = client.post(
        "/auth/v1/register",
        json={
            "name": "Mauri",
            "lastname": "Salinas",
            "email": "user+tag@mail.com",
            "password": "plain1234",
            "birthdate": "2000-01-01",
        },
    )

    assert response.status_code == 400
    assert response.json()["message"] == "Validation error"
    assert register_use_case.received is None


# Tipo de test: Integration
def test_should_return_401_when_login_credentials_are_invalid() -> None:
    """Valida que login retorna 401 cuando las credenciales son inválidas."""
    client = create_test_client()
    login_use_case = StubUseCase(error=InvalidCredentialsException())
    client.app.dependency_overrides[get_login_user_use_case] = lambda: login_use_case

    response = client.post(
        "/auth/v1/login",
        data={"username": "mauri@mail.com", "password": "bad"},
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password"


# Tipo de test: Integration
def test_should_return_401_when_login_email_format_is_invalid() -> None:
    """Valida que login retorna 401 con email malformado según policy y no consulta datasource."""
    client = create_test_client()

    auth_datasource = Mock(spec=AuthDatasource)
    password_manager = Mock(spec=PasswordManager)
    token_manager = Mock(spec=TokenManager)
    token_revocation_store = Mock(spec=TokenRevocationStore)
    login_use_case = LoginUser(auth_datasource, password_manager, token_manager, token_revocation_store)
    client.app.dependency_overrides[get_login_user_use_case] = lambda: login_use_case

    response = client.post(
        "/auth/v1/login",
        data={"username": "user+tag@mail.com", "password": "bad"},
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password"
    auth_datasource.get_user_by_email.assert_not_called()
