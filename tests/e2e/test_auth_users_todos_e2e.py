from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.providers.db import get_db_session
from app.features.auth.application.contracts.email_sender import EmailSender
from app.features.auth.di.dependencies import get_email_sender, get_rate_limiter
from app.features.auth.infrastructure.security.in_memory_rate_limiter import InMemoryRateLimiter
from app.main import app


def _override_db_session(session: Session):
    """Vincula la dependencia de base de datos de la app a la sesion de prueba."""

    def _provider() -> Generator[Session, None, None]:
        yield session

    return _provider


def _register_user(
    client: TestClient, *, name: str, lastname: str, email: str, password: str
) -> dict:
    response = client.post(
        "/auth/v1/register",
        json={
            "name": name,
            "lastname": lastname,
            "email": email,
            "password": password,
            "birthdate": "2000-01-01",
        },
    )
    assert response.status_code == 201
    return response.json()


def _login_user(client: TestClient, *, email: str, password: str) -> dict:
    response = client.post(
        "/auth/v1/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


class CaptureEmailSender(EmailSender):
    def __init__(self) -> None:
        self.last_otp_code: str | None = None

    def send_otp(self, to_email: str, code: str, purpose: str) -> None:
        self.last_otp_code = code


# E2E happy path: register -> login -> protected endpoints -> refresh -> continue with new token.
# Tipo de test: E2E
def test_should_complete_auth_users_todos_happy_path(db_session: Session) -> None:
    """Valida que completa el flujo exitoso de autenticacion, usuarios y tareas."""
    app.dependency_overrides[get_db_session] = _override_db_session(db_session)
    client = TestClient(app, raise_server_exceptions=False)

    try:
        register_payload = _register_user(
            client,
            name="Mauri",
            lastname="Salinas",
            email="mauri@mail.com",
            password="pass1234",
        )
        user_id = register_payload["user"]["id"]

        login_payload = _login_user(client, email="mauri@mail.com", password="pass1234")
        access_token = login_payload["access_token"]
        refresh_token = login_payload["refresh_token"]

        update_user_response = client.put(
            f"/v1/users/{user_id}",
            headers=_auth_headers(access_token),
            json={
                "name": "Mauricio",
                "lastname": "Salinas",
                "email": "mauri@mail.com",
                "birthdate": "2000-01-01",
            },
        )
        assert update_user_response.status_code == 200

        me_response = client.get("/auth/v1/me", headers=_auth_headers(access_token))
        assert me_response.status_code == 200
        assert me_response.json()["user"]["id"] == user_id

        users_response = client.get("/v1/users", headers=_auth_headers(access_token))
        assert users_response.status_code == 200
        assert len(users_response.json()["users"]) == 1

        create_todo_response = client.post(
            "/v1/todos",
            headers=_auth_headers(access_token),
            json={"title": "Study", "description": "Study clean architecture"},
        )
        assert create_todo_response.status_code == 201
        todo_id = create_todo_response.json()["todo"]["id"]

        list_todos_response = client.get("/v1/todos", headers=_auth_headers(access_token))
        assert list_todos_response.status_code == 200
        assert len(list_todos_response.json()["todos"]) == 1

        update_todo_response = client.put(
            f"/v1/todos/{todo_id}",
            headers=_auth_headers(access_token),
            json={
                "title": "Study DDD",
                "description": "Study clean architecture and DDD",
                "is_completed": True,
            },
        )
        assert update_todo_response.status_code == 200
        assert update_todo_response.json()["todo"]["is_completed"] is True

        refresh_response = client.post("/auth/v1/refresh", json={"refresh_token": refresh_token})
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.json()["tokens"]["access_token"]

        list_with_new_token_response = client.get(
            "/v1/todos", headers=_auth_headers(new_access_token)
        )
        assert list_with_new_token_response.status_code == 200

        delete_todo_response = client.delete(
            f"/v1/todos/{todo_id}", headers=_auth_headers(new_access_token)
        )
        assert delete_todo_response.status_code == 200

        get_deleted_response = client.get(
            f"/v1/todos/{todo_id}", headers=_auth_headers(new_access_token)
        )
        assert get_deleted_response.status_code == 404
    finally:
        app.dependency_overrides.clear()


# E2E error path: unauthorized access, duplicate register and cross-user ownership protection.
# Tipo de test: E2E
def test_should_enforce_auth_and_ownership_error_scenarios(db_session: Session) -> None:
    """Valida que aplica reglas de autenticacion y propiedad en escenarios de error."""
    app.dependency_overrides[get_db_session] = _override_db_session(db_session)
    client = TestClient(app, raise_server_exceptions=False)

    try:
        unauthorized_response = client.get("/v1/todos")
        assert unauthorized_response.status_code == 401

        register_payload = _register_user(
            client,
            name="Mauri",
            lastname="Salinas",
            email="mauri@mail.com",
            password="pass1234",
        )
        user_id = register_payload["user"]["id"]

        duplicate_register_response = client.post(
            "/auth/v1/register",
            json={
                "name": "Mauri",
                "lastname": "Salinas",
                "email": "mauri@mail.com",
                "password": "pass1234",
                "birthdate": "2000-01-01",
            },
        )
        assert duplicate_register_response.status_code == 409

        login_user_one = _login_user(client, email="mauri@mail.com", password="pass1234")
        token_user_one = login_user_one["access_token"]

        todo_response = client.post(
            "/v1/todos",
            headers=_auth_headers(token_user_one),
            json={"title": "Private", "description": "Owner only"},
        )
        assert todo_response.status_code == 201
        todo_id = todo_response.json()["todo"]["id"]

        _register_user(
            client,
            name="Ana",
            lastname="Lopez",
            email="ana@mail.com",
            password="pass5678",
        )
        login_user_two = _login_user(client, email="ana@mail.com", password="pass5678")
        token_user_two = login_user_two["access_token"]

        cross_owner_read_response = client.get(
            f"/v1/todos/{todo_id}",
            headers=_auth_headers(token_user_two),
        )
        assert cross_owner_read_response.status_code == 404

        invalid_token_response = client.get(
            "/v1/todos",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert invalid_token_response.status_code == 401

        invalid_email_response = client.put(
            f"/v1/users/{user_id}",
            headers=_auth_headers(token_user_one),
            json={
                "name": "Mauri",
                "lastname": "Salinas",
                "email": "user+tag@mail.com",
                "birthdate": "2000-01-01",
            },
        )
        assert invalid_email_response.status_code == 400
    finally:
        app.dependency_overrides.clear()


# Tipo de test: E2E
def test_should_change_password_with_otp_and_reject_reused_code(db_session: Session) -> None:
    """Valida flujo real: request otp -> change password -> login nuevo -> rechaza OTP reutilizado."""
    app.dependency_overrides[get_db_session] = _override_db_session(db_session)
    capture_email_sender = CaptureEmailSender()
    app.dependency_overrides[get_email_sender] = lambda: capture_email_sender
    app.dependency_overrides[get_rate_limiter] = lambda: InMemoryRateLimiter()
    client = TestClient(app, raise_server_exceptions=False)

    try:
        _register_user(
            client,
            name="Mauri",
            lastname="Salinas",
            email="mauri@mail.com",
            password="pass1234",
        )
        old_login_payload = _login_user(client, email="mauri@mail.com", password="pass1234")
        old_access_token = old_login_payload["access_token"]

        request_otp_response = client.post(
            "/auth/v1/request-otp",
            headers=_auth_headers(old_access_token),
        )
        assert request_otp_response.status_code == 200
        assert capture_email_sender.last_otp_code is not None
        otp_code = capture_email_sender.last_otp_code

        change_password_response = client.post(
            "/auth/v1/change-password",
            headers=_auth_headers(old_access_token),
            json={"code": otp_code, "new_password": "newpass1234"},
        )
        assert change_password_response.status_code == 200

        old_password_login_response = client.post(
            "/auth/v1/login",
            data={"username": "mauri@mail.com", "password": "pass1234"},
        )
        assert old_password_login_response.status_code == 401

        new_login_payload = _login_user(client, email="mauri@mail.com", password="newpass1234")
        new_access_token = new_login_payload["access_token"]

        reuse_otp_response = client.post(
            "/auth/v1/change-password",
            headers=_auth_headers(new_access_token),
            json={"code": otp_code, "new_password": "anotherpass1234"},
        )
        assert reuse_otp_response.status_code == 401
    finally:
        app.dependency_overrides.clear()


# Tipo de test: E2E
def test_should_rate_limit_change_password_attempts(db_session: Session) -> None:
    """Valida que /change-password aplica rate limit y retorna 429 al exceder intentos."""
    app.dependency_overrides[get_db_session] = _override_db_session(db_session)
    limiter = InMemoryRateLimiter()
    app.dependency_overrides[get_rate_limiter] = lambda: limiter
    client = TestClient(app, raise_server_exceptions=False)

    try:
        _register_user(
            client,
            name="Mauri",
            lastname="Salinas",
            email="mauri@mail.com",
            password="pass1234",
        )
        login_payload = _login_user(client, email="mauri@mail.com", password="pass1234")
        access_token = login_payload["access_token"]

        for _ in range(5):
            response = client.post(
                "/auth/v1/change-password",
                headers=_auth_headers(access_token),
                json={"code": "000000", "new_password": "newpass1234"},
            )
            assert response.status_code == 401

        rate_limited_response = client.post(
            "/auth/v1/change-password",
            headers=_auth_headers(access_token),
            json={"code": "000000", "new_password": "newpass1234"},
        )
        assert rate_limited_response.status_code == 429
    finally:
        app.dependency_overrides.clear()
