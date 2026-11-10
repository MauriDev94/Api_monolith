# mypy: disable-error-code="attr-defined"
# Reason: `fastapi.testclient.TestClient`'s class-as-callable signature trips
# `mypy --follow-imports=silent` in per-file mode (it shows `client` as the
# `__init__` Callable, not an instance). Project-scope `mypy app` is unaffected;
# this directive scopes the suppression to this file only.

from __future__ import annotations

import secrets
from collections.abc import Callable
from datetime import date
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response

from app.core.exceptions.error_handling import register_exception_handlers
from app.core.exceptions.exceptions import (
    ConflictError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
)
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.rate_limiter import RateLimiter
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.dto.token_pair_result import TokenPairResult
from app.features.auth.application.usecases.handle_google_callback import (
    HandleGoogleCallbackUseCase,
)
from app.features.auth.application.usecases.initiate_google_login import (
    InitiateGoogleLoginResult,
    InitiateGoogleLoginUseCase,
)
from app.features.auth.application.usecases.login_user_use_case import LoginUser
from app.features.auth.application.usecases.refresh_access_token_use_case import (
    RefreshAccessToken,
)
from app.features.auth.di.dependencies import (
    get_change_password_with_otp_use_case,
    get_handle_google_callback_use_case,
    get_initiate_google_login_use_case,
    get_link_google_account_use_case,
    get_login_user_use_case,
    get_logout_use_case,
    get_rate_limiter,
    get_refresh_access_token_use_case,
    get_register_user_use_case,
    get_request_otp_use_case,
)
from app.features.auth.domain.value_objects.otp_purpose import OtpPurpose
from app.features.auth.presentation import api as auth_api
from app.features.auth.presentation.api import v1_router
from app.features.auth.presentation.security_dependencies import get_authenticated_user
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


class StubUseCase:
    def __init__(
        self,
        result: object = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.received: object = None

    def execute(self, params: object = None) -> object:
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
    assert request_otp_use_case.received.purpose == OtpPurpose.PASSWORD_CHANGE


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
def test_google_init_disables_caching_when_state_is_issued() -> None:
    """The OAuth state is a secret (Set-Cookie and authorization_url): never cacheable."""
    client = create_test_client()
    state = secrets.token_urlsafe(16)
    use_case = Mock(spec=InitiateGoogleLoginUseCase)
    use_case.execute.return_value = InitiateGoogleLoginResult(
        authorization_url=f"https://accounts.google.com/o/oauth2/v2/auth?state={state}",
        state=state,
    )
    client.app.dependency_overrides[get_initiate_google_login_use_case] = lambda: use_case

    response = client.get("/auth/v1/google")

    assert response.status_code == 200
    assert f"oauth_state={state}" in response.headers["set-cookie"]
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"


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


# Tipo de test: Integration
def test_should_return_409_when_link_google_is_already_linked() -> None:
    client = create_test_client()
    link_google_use_case = StubUseCase(
        error=ConflictError("Google account already linked to this user")
    )
    client.app.dependency_overrides[get_link_google_account_use_case] = lambda: link_google_use_case
    client.app.dependency_overrides[get_authenticated_user] = make_user

    response = client.post(
        "/auth/v1/link-google",
        json={"google_id": "google-id-123", "password": "pass1234"},
    )

    assert response.status_code == 409
    assert response.json()["message"] == "Google account already linked to this user"


# === Refresh cookie transport + /logout (BE-007) ===
#
# These tests pin the wire contract the frontend relies on:
# - Login sets an HttpOnly refresh cookie with the expected attrs.
# - The refresh cookie is the ONLY refresh transport: it never appears in a response
#   body, and /refresh ignores any request body (a body-only token gets a 401).
# - Token responses (login, refresh, Google callback) carry Cache-Control: no-store
#   and Pragma: no-cache (RFC 6749 section 5.1).
# - /logout is idempotent: the endpoint always invokes LogoutUseCase with the raw
#   cookie (or None) and the use case owns the decode/revoke decision. The
#   endpoint is responsible for emitting a Set-Cookie Max-Age=0 to wipe any
#   residual browser state.

_REFRESH_COOKIE_KEY = "refresh_token"


def _token_pair() -> TokenPairResult:
    """Fresh, random token pair (never hardcode token-like values in tests)."""
    return TokenPairResult(
        access_token=secrets.token_urlsafe(16), refresh_token=secrets.token_urlsafe(16)
    )


def _login_form() -> dict[str, str]:
    return {"username": "mauri@mail.com", "password": secrets.token_urlsafe(12)}


def _mock_login(client: TestClient, result: TokenPairResult) -> Mock:
    use_case = Mock(spec=LoginUser)
    use_case.execute.return_value = result
    client.app.dependency_overrides[get_login_user_use_case] = lambda: use_case
    return use_case


def _mock_refresh(client: TestClient, result: TokenPairResult) -> Mock:
    use_case = Mock(spec=RefreshAccessToken)
    use_case.execute.return_value = result
    client.app.dependency_overrides[get_refresh_access_token_use_case] = lambda: use_case
    return use_case


def _mock_google_callback(client: TestClient, result: TokenPairResult) -> Mock:
    use_case = Mock(spec=HandleGoogleCallbackUseCase)
    use_case.execute.return_value = result
    client.app.dependency_overrides[get_handle_google_callback_use_case] = lambda: use_case
    return use_case


def _get_google_callback(client: TestClient) -> Response:
    state = secrets.token_urlsafe(16)
    client.cookies.set("oauth_state", state)
    return client.get(
        "/auth/v1/google/callback", params={"code": secrets.token_urlsafe(8), "state": state}
    )


def _assert_cookie_only_token_response(response: Response, result: TokenPairResult) -> None:
    """The refresh token is in Set-Cookie only, and the response must not be cacheable."""
    assert response.status_code == 200
    assert "refresh_token" not in response.text
    assert result.refresh_token not in response.text
    assert f"{_REFRESH_COOKIE_KEY}={result.refresh_token}" in response.headers["set-cookie"]
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["pragma"] == "no-cache"


# Tipo de test: Integration
def test_login_sets_refresh_cookie_with_expected_attrs() -> None:
    """Login must set refresh_token cookie with HttpOnly + Max-Age=7d + Path=/."""
    client = create_test_client()
    result = _token_pair()
    _mock_login(client, result)

    response = client.post("/auth/v1/login", data=_login_form())

    assert response.status_code == 200
    # The body carries the access token only; the refresh token is cookie-only.
    assert response.json() == {"access_token": result.access_token, "token_type": "bearer"}

    set_cookie = response.headers.get("set-cookie", "")
    assert _REFRESH_COOKIE_KEY in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Max-Age=604800" in set_cookie
    assert "Path=/" in set_cookie

    # Client-side cookie jar must reflect the new refresh cookie.
    assert client.cookies.get(_REFRESH_COOKIE_KEY) == result.refresh_token


# Tipo de test: Integration
def test_login_omits_refresh_token_from_body_and_disables_caching_when_credentials_are_valid() -> (
    None
):
    """Login: no refresh_token in the body, Set-Cookie present, no-store + no-cache."""
    client = create_test_client()
    result = _token_pair()
    _mock_login(client, result)

    response = client.post("/auth/v1/login", data=_login_form())

    _assert_cookie_only_token_response(response, result)


# Tipo de test: Integration
def test_refresh_omits_refresh_token_from_body_and_disables_caching_when_cookie_is_valid() -> None:
    """Refresh: body is tokens/access_token/token_type, cookie rotated, no-store."""
    client = create_test_client()
    result = _token_pair()
    _mock_refresh(client, result)
    client.cookies.set(_REFRESH_COOKIE_KEY, secrets.token_urlsafe(16))

    response = client.post("/auth/v1/refresh")

    _assert_cookie_only_token_response(response, result)
    assert response.json() == {
        "tokens": {"access_token": result.access_token, "token_type": "bearer"}
    }


# Tipo de test: Integration
def test_google_callback_omits_refresh_token_from_body_and_disables_caching_when_state_matches() -> (
    None
):
    """Google callback: no refresh_token in the body, Set-Cookie present, no-store."""
    client = create_test_client()
    result = _token_pair()
    _mock_google_callback(client, result)

    response = _get_google_callback(client)

    _assert_cookie_only_token_response(response, result)
    assert response.json() == {"access_token": result.access_token, "token_type": "bearer"}


# SameSite/Secure depend on APP_ENV: browsers reject `SameSite=None` without
# `Secure`, so dev (HTTP) uses Lax and production (HTTPS, cross-site) uses None+Secure.
_COOKIE_ENV_CASES = [
    pytest.param(False, "samesite=lax", id="dev"),
    pytest.param(True, "samesite=none", id="production"),
]


def _post_login(client: TestClient) -> str:
    _mock_login(client, _token_pair())
    response = client.post("/auth/v1/login", data=_login_form())
    assert response.status_code == 200
    return response.headers.get("set-cookie", "")


def _post_refresh(client: TestClient) -> str:
    _mock_refresh(client, _token_pair())
    client.cookies.set(_REFRESH_COOKIE_KEY, secrets.token_urlsafe(16))
    response = client.post("/auth/v1/refresh")
    assert response.status_code == 200
    return response.headers.get("set-cookie", "")


def _post_logout(client: TestClient) -> str:
    client.app.dependency_overrides[get_logout_use_case] = lambda: StubUseCase(result=None)
    client.app.dependency_overrides[get_rate_limiter] = lambda: StubRateLimiter()
    response = client.post("/auth/v1/logout")
    assert response.status_code == 204
    return response.headers.get("set-cookie", "")


# Tipo de test: Integration
@pytest.mark.parametrize("send", [_post_login, _post_refresh, _post_logout])
@pytest.mark.parametrize(("secure", "expected_samesite"), _COOKIE_ENV_CASES)
def test_refresh_cookie_samesite_and_secure_follow_app_env(
    monkeypatch: pytest.MonkeyPatch,
    send: Callable[[TestClient], str],
    secure: bool,
    expected_samesite: str,
) -> None:
    """Dev → `SameSite=lax` without Secure; production → `SameSite=none; Secure`."""
    monkeypatch.setattr(auth_api, "_OAUTH_COOKIE_SECURE", secure)
    client = create_test_client()

    set_cookie = send(client).lower()

    assert _REFRESH_COOKIE_KEY in set_cookie
    assert expected_samesite in set_cookie
    assert ("; secure" in set_cookie) is secure


# Tipo de test: Integration
def test_refresh_uses_cookie_value_when_cookie_is_present() -> None:
    """The use case receives the cookie value verbatim and rotation emits a new cookie."""
    client = create_test_client()
    result = _token_pair()
    use_case = _mock_refresh(client, result)
    cookie_value = secrets.token_urlsafe(16)
    client.cookies.set(_REFRESH_COOKIE_KEY, cookie_value)

    response = client.post("/auth/v1/refresh")

    assert response.status_code == 200
    assert use_case.execute.call_args.args[0].refresh_token == cookie_value
    assert f"{_REFRESH_COOKIE_KEY}={result.refresh_token}" in response.headers["set-cookie"]


# Tipo de test: Integration
def test_refresh_ignores_empty_json_body_when_cookie_is_present() -> None:
    """The current frontend POSTs `{}`: an undeclared body must not break the cookie flow."""
    client = create_test_client()
    use_case = _mock_refresh(client, _token_pair())
    cookie_value = secrets.token_urlsafe(16)
    client.cookies.set(_REFRESH_COOKIE_KEY, cookie_value)

    response = client.post("/auth/v1/refresh", json={})

    assert response.status_code == 200
    assert use_case.execute.call_args.args[0].refresh_token == cookie_value


# Tipo de test: Integration
def test_refresh_ignores_body_token_when_cookie_is_present() -> None:
    """A token in the body never overrides (nor replaces) the cookie."""
    client = create_test_client()
    use_case = _mock_refresh(client, _token_pair())
    cookie_value = secrets.token_urlsafe(16)
    client.cookies.set(_REFRESH_COOKIE_KEY, cookie_value)

    response = client.post("/auth/v1/refresh", json={"refresh_token": secrets.token_urlsafe(16)})

    assert response.status_code == 200
    assert use_case.execute.call_args.args[0].refresh_token == cookie_value


# Tipo de test: Integration
def test_refresh_returns_401_when_token_is_only_in_the_body() -> None:
    """The body is not a transport anymore: body-only token → 401, use case not called."""
    client = create_test_client()
    use_case = _mock_refresh(client, _token_pair())

    response = client.post("/auth/v1/refresh", json={"refresh_token": secrets.token_urlsafe(16)})

    assert response.status_code == 401
    assert response.json()["message"] == "refresh_token required"
    assert "set-cookie" not in response.headers
    use_case.execute.assert_not_called()


# Tipo de test: Integration
@pytest.mark.parametrize("body", [None, {}], ids=["no-body", "empty-json-body"])
def test_refresh_returns_401_without_cookies_or_token_headers_when_cookie_is_absent(
    body: dict[str, str] | None,
) -> None:
    """No cookie is an auth failure (401), not a validation error (400), with or without body."""
    client = create_test_client()
    use_case = _mock_refresh(client, _token_pair())

    response = (
        client.post("/auth/v1/refresh", json=body)
        if body is not None
        else client.post("/auth/v1/refresh")
    )

    assert response.status_code == 401
    assert "set-cookie" not in response.headers
    assert "cache-control" not in response.headers
    assert "pragma" not in response.headers
    use_case.execute.assert_not_called()


# Tipo de test: Integration
def test_logout_returns_204_and_calls_use_case_when_cookie_is_valid() -> None:
    """The endpoint forwards the raw cookie to LogoutUseCase and clears the cookie.

    The endpoint is intentionally ignorant of JWT internals — decode/revoke
    decisions live inside the use case.
    """
    client = create_test_client()
    logout_use_case = StubUseCase(result=None)
    client.app.dependency_overrides[get_logout_use_case] = lambda: logout_use_case
    client.app.dependency_overrides[get_rate_limiter] = lambda: StubRateLimiter()
    client.cookies.set(_REFRESH_COOKIE_KEY, "valid-refresh")

    response = client.post("/auth/v1/logout")

    assert response.status_code == 204
    assert response.content == b""
    # StubUseCase.received is set inside execute(); its presence proves the
    # endpoint dispatched to the use case with the cookie verbatim.
    assert logout_use_case.received.refresh_token == "valid-refresh"

    set_cookie = response.headers.get("set-cookie", "")
    assert "Max-Age=0" in set_cookie
    assert "Path=/" in set_cookie


# Tipo de test: Integration
def test_logout_returns_204_when_cookie_is_absent() -> None:
    """Idempotency: no cookie → 204; the use case still runs with None and clears.

    The endpoint always invokes the use case (the use case handles the no-op
    internally) and still emits a Set-Cookie Max-Age=0 to wipe residual state.
    """
    client = create_test_client()
    logout_use_case = StubUseCase(result=None)
    client.app.dependency_overrides[get_logout_use_case] = lambda: logout_use_case
    client.app.dependency_overrides[get_rate_limiter] = lambda: StubRateLimiter()

    response = client.post("/auth/v1/logout")

    assert response.status_code == 204
    assert logout_use_case.received.refresh_token is None
    # Clear is still emitted so any residual browser state is wiped.
    assert "Max-Age=0" in response.headers.get("set-cookie", "")


# Tipo de test: Integration
def test_logout_returns_429_when_rate_limit_is_exceeded() -> None:
    """Logging out faster than 30/min per IP must return 429."""
    client = create_test_client()
    logout_use_case = StubUseCase(result=None)
    limiter = StubRateLimiter()
    client.app.dependency_overrides[get_logout_use_case] = lambda: logout_use_case
    client.app.dependency_overrides[get_rate_limiter] = lambda: limiter

    for _ in range(30):
        response = client.post("/auth/v1/logout")
        assert response.status_code == 204

    response = client.post("/auth/v1/logout")
    assert response.status_code == 429
