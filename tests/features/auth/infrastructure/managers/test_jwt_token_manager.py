import pytest

from app.core.exceptions.exceptions import InvalidCredentialsException
from app.features.auth.infrastructure.managers.jwt_token_manager import JwtTokenManager


def test_should_create_and_decode_access_token() -> None:
    manager = JwtTokenManager(secret_key="secret-key")

    token = manager.create_access_token(subject="user-1")
    payload = manager.decode_access_token(token)

    assert payload["sub"] == "user-1"
    assert payload["token_type"] == "access"


def test_should_raise_invalid_credentials_when_decoding_invalid_token() -> None:
    manager = JwtTokenManager(secret_key="secret-key")

    with pytest.raises(InvalidCredentialsException):
        manager.decode_access_token("invalid.token.value")


def test_should_raise_invalid_credentials_when_token_type_is_wrong() -> None:
    manager = JwtTokenManager(secret_key="secret-key")
    refresh_token = manager.create_refresh_token(subject="user-1")

    with pytest.raises(InvalidCredentialsException):
        manager.decode_access_token(refresh_token)
