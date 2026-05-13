"""Tests for GoogleOAuthProviderImpl user info parsing."""

from unittest.mock import MagicMock, patch

from app.core.config.env_config import EnvConfig
from app.features.auth.infrastructure.providers.google_oauth_provider import GoogleOAuthProviderImpl


def _build_provider() -> GoogleOAuthProviderImpl:
    config = EnvConfig(
        db_user="u",
        db_password="p",
        db_name="d",
        db_port=5432,
        db_host="localhost",
        jwt_secret_key="secret",
        google_client_id="client-id",
        google_client_secret="client-secret",
        google_redirect_uri="http://localhost/callback",
    )
    return GoogleOAuthProviderImpl(config=config)


@patch("app.features.auth.infrastructure.providers.google_oauth_provider.httpx.Client")
def test_should_use_given_and_family_name_when_google_provides_them(
    mock_client_cls: MagicMock,
) -> None:
    provider = _build_provider()

    response = MagicMock()
    response.json.return_value = {
        "sub": "g-1",
        "email": "user@gmail.com",
        "name": "María José García López",
        "given_name": "María José",
        "family_name": "García López",
        "email_verified": True,
    }
    client = MagicMock()
    client.get.return_value = response
    mock_client_cls.return_value.__enter__.return_value = client

    result = provider.get_user_info("access", "id")

    assert result.name == "María José"
    assert result.lastname == "García López"


@patch("app.features.auth.infrastructure.providers.google_oauth_provider.httpx.Client")
def test_should_fallback_to_split_full_name_when_structured_fields_are_missing(
    mock_client_cls: MagicMock,
) -> None:
    provider = _build_provider()

    response = MagicMock()
    response.json.return_value = {
        "sub": "g-2",
        "email": "user@gmail.com",
        "name": "Juan Pérez Soto",
        "email_verified": True,
    }
    client = MagicMock()
    client.get.return_value = response
    mock_client_cls.return_value.__enter__.return_value = client

    result = provider.get_user_info("access", "id")

    assert result.name == "Juan"
    assert result.lastname == "Pérez Soto"


@patch("app.features.auth.infrastructure.providers.google_oauth_provider.httpx.Client")
def test_should_handle_name_without_lastname_when_structured_fields_are_missing(
    mock_client_cls: MagicMock,
) -> None:
    provider = _build_provider()

    response = MagicMock()
    response.json.return_value = {
        "sub": "g-3",
        "email": "user@gmail.com",
        "name": "Madonna",
        "email_verified": True,
    }
    client = MagicMock()
    client.get.return_value = response
    mock_client_cls.return_value.__enter__.return_value = client

    result = provider.get_user_info("access", "id")

    assert result.name == "Madonna"
    assert result.lastname == ""
