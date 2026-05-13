from datetime import date
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions.error_handling import register_exception_handlers
from app.core.exceptions.exceptions import NotFoundError, TooManyRequestsError, UnauthorizedError
from app.features.auth.application.constants import OTP_PURPOSE_PASSWORD_CHANGE
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.rate_limiter import RateLimiter
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.usecases.initiate_google_login import InitiateGoogleLoginResult
from app.features.auth.application.usecases.login_user_use_case import LoginUser
from app.features.auth.di.dependencies import (
    get_change_password_with_otp_use_case,
    get_initiate_google_login_use_case,
    get_login_user_use_case,
    get_rate_limiter,
    get_register_user_use_case,
    get_request_otp_use_case,
    get_verify_otp_use_case,
)
from app.features.auth.presentation.api import v1_router
from app.features.auth.presentation.security_dependencies import get_authenticated_user
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


class StubRateLimiter(RateLimiter):
    def __init__(self) -> None:
        self.hits: dict[str, int] = {}

    def check_or_raise(self, key: str, limit: int, window_seconds: int) -> None:
        count = self.hits.get(key, 0) + 1
        self.hits[key] = count
        if count > limit:
            raise TooManyRequestsError("Too many requests, try again later")


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
            "email": "invalid-mail",
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
    login_use_case = StubUseCase(error=UnauthorizedError("Invalid email or password"))
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
    login_use_case = LoginUser(
        auth_datasource, password_manager, token_manager, token_revocation_store
    )
    client.app.dependency_overrides[get_login_user_use_case] = lambda: login_use_case

    response = client.post(
        "/auth/v1/login",
        data={"username": "invalid-mail", "password": "bad"},
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password"
    auth_datasource.get_user_by_email.assert_not_called()


# Tipo de test: Integration
def test_should_return_200_when_request_otp_is_valid() -> None:
    client = create_test_client()
    request_otp_use_case = StubUseCase(result=None)
    client.app.dependency_overrides[get_request_otp_use_case] = lambda: request_otp_use_case
    client.app.dependency_overrides[get_rate_limiter] = lambda: StubRateLimiter()
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.post(
        "/auth/v1/request-otp",
    )

    assert response.status_code == 200
    assert response.json() == {"message": "OTP sent"}
    assert request_otp_use_case.received.user_id == "user-1"
    assert request_otp_use_case.received.purpose == OTP_PURPOSE_PASSWORD_CHANGE


# Tipo de test: Integration
def test_should_return_404_when_request_otp_user_not_found() -> None:
    client = create_test_client()
    request_otp_use_case = StubUseCase(error=NotFoundError("user not found"))
    client.app.dependency_overrides[get_request_otp_use_case] = lambda: request_otp_use_case
    client.app.dependency_overrides[get_rate_limiter] = lambda: StubRateLimiter()
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.post(
        "/auth/v1/request-otp",
    )

    assert response.status_code == 404
    assert response.json()["message"] == "user not found"


# Tipo de test: Integration
def test_should_return_200_when_verify_otp_is_valid() -> None:
    client = create_test_client()
    verify_otp_use_case = StubUseCase(result=None)
    client.app.dependency_overrides[get_verify_otp_use_case] = lambda: verify_otp_use_case
    client.app.dependency_overrides[get_rate_limiter] = lambda: StubRateLimiter()
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.post(
        "/auth/v1/verify-otp",
        json={"code": "123456"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "OTP verified"}
    assert verify_otp_use_case.received.user_id == "user-1"
    assert verify_otp_use_case.received.code == "123456"
    assert verify_otp_use_case.received.purpose == OTP_PURPOSE_PASSWORD_CHANGE


# Tipo de test: Integration
def test_should_return_401_when_verify_otp_is_invalid() -> None:
    client = create_test_client()
    verify_otp_use_case = StubUseCase(error=UnauthorizedError("Invalid otp code"))
    client.app.dependency_overrides[get_verify_otp_use_case] = lambda: verify_otp_use_case
    client.app.dependency_overrides[get_rate_limiter] = lambda: StubRateLimiter()
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.post(
        "/auth/v1/verify-otp",
        json={"code": "123456"},
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid otp code"


# Tipo de test: Integration
def test_should_return_429_when_request_otp_rate_limit_is_exceeded() -> None:
    client = create_test_client()
    request_otp_use_case = StubUseCase(result=None)
    limiter = StubRateLimiter()
    client.app.dependency_overrides[get_request_otp_use_case] = lambda: request_otp_use_case
    client.app.dependency_overrides[get_rate_limiter] = lambda: limiter
    client.app.dependency_overrides[get_authenticated_user] = make_user

    for _ in range(3):
        response = client.post("/auth/v1/request-otp")
        assert response.status_code == 200

    response = client.post("/auth/v1/request-otp")

    assert response.status_code == 429


# Tipo de test: Integration
def test_should_return_200_when_change_password_with_otp_is_valid() -> None:
    client = create_test_client()
    change_password_use_case = StubUseCase(result=None)
    client.app.dependency_overrides[get_change_password_with_otp_use_case] = lambda: (
        change_password_use_case
    )
    client.app.dependency_overrides[get_rate_limiter] = lambda: StubRateLimiter()
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.post(
        "/auth/v1/change-password",
        json={"code": "123456", "new_password": "new-password-123"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Password changed. Please login again"}
    assert change_password_use_case.received.user_id == "user-1"
    assert change_password_use_case.received.code == "123456"
    assert change_password_use_case.received.new_password == "new-password-123"


# Tipo de test: Integration
def test_should_return_200_with_authorization_url_when_initiating_google_login() -> None:
    client = create_test_client()
    initiate_google_use_case = StubUseCase(
        result=InitiateGoogleLoginResult(
            authorization_url="https://accounts.google.com/o/oauth2/v2/auth?state=abc",
            state="abc",
        )
    )
    client.app.dependency_overrides[get_initiate_google_login_use_case] = lambda: (
        initiate_google_use_case
    )

    response = client.get("/auth/v1/google")

    assert response.status_code == 200
    assert response.json() == {
        "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?state=abc"
    }
    assert response.headers.get("location") is None


# Tipo de test: Integration
def test_should_return_401_when_change_password_otp_is_invalid() -> None:
    client = create_test_client()
    change_password_use_case = StubUseCase(error=UnauthorizedError("Invalid otp code"))
    client.app.dependency_overrides[get_change_password_with_otp_use_case] = lambda: (
        change_password_use_case
    )
    client.app.dependency_overrides[get_rate_limiter] = lambda: StubRateLimiter()
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.post(
        "/auth/v1/change-password",
        json={"code": "123456", "new_password": "new-password-123"},
    )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid otp code"
