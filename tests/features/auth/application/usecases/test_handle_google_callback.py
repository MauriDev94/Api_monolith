"""Tests for HandleGoogleCallbackUseCase."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.core.exceptions.exceptions import ConflictError
from app.features.auth.application.contracts.google_auth_datasource import GoogleAuthDatasource
from app.features.auth.application.contracts.oauth_provider import (
    GoogleTokenData,
    GoogleUserInfo,
    OAuthProvider,
)
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.usecases.handle_google_callback import (
    HandleGoogleCallbackParams,
    HandleGoogleCallbackUseCase,
)
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


class TestHandleGoogleCallbackUseCase:
    """Unit tests for HandleGoogleCallbackUseCase."""

    @pytest.fixture
    def mock_oauth_provider(self) -> MagicMock:
        """Create a mock OAuth provider."""
        provider = MagicMock(spec=OAuthProvider)
        provider.exchange_code.return_value = GoogleTokenData(
            access_token="test-access-token",
            id_token="test-id-token",
        )
        provider.get_user_info.return_value = GoogleUserInfo(
            google_id="google-user-123",
            email="newuser@gmail.com",
            name="New",
            lastname="User",
            email_verified=True,
        )
        return provider

    @pytest.fixture
    def mock_google_auth_datasource(self) -> MagicMock:
        """Create a mock Google auth datasource."""
        datasource = MagicMock(spec=GoogleAuthDatasource)
        datasource.get_user_by_google_id.return_value = None
        datasource.get_user_by_email.return_value = None
        return datasource

    @pytest.fixture
    def mock_token_manager(self) -> MagicMock:
        """Create a mock token manager."""
        manager = MagicMock(spec=TokenManager)
        manager.create_access_token.return_value = "mock-access-token"
        manager.create_refresh_token.return_value = "mock-refresh-token"
        manager.decode_refresh_token.return_value = {"exp": 1234567890}
        return manager

    @pytest.fixture
    def mock_token_revocation_store(self) -> MagicMock:
        """Create a mock token revocation store."""
        return MagicMock(spec=TokenRevocationStore)

    @pytest.fixture
    def use_case(
        self,
        mock_oauth_provider: MagicMock,
        mock_google_auth_datasource: MagicMock,
        mock_token_manager: MagicMock,
        mock_token_revocation_store: MagicMock,
    ) -> HandleGoogleCallbackUseCase:
        """Create the use case with mocked dependencies."""
        return HandleGoogleCallbackUseCase(
            oauth_provider=mock_oauth_provider,
            google_auth_datasource=mock_google_auth_datasource,
            token_manager=mock_token_manager,
            token_revocation_store=mock_token_revocation_store,
        )

    def test_should_create_new_user_when_not_found_by_google_id_or_email(
        self,
        use_case: HandleGoogleCallbackUseCase,
        mock_google_auth_datasource: MagicMock,
    ) -> None:
        """Test that a new user is created when no existing user is found."""
        params = HandleGoogleCallbackParams(code="test-code")

        result = use_case.execute(params)

        mock_google_auth_datasource.create_google_user.assert_called_once()
        assert result.access_token == "mock-access-token"
        assert result.refresh_token == "mock-refresh-token"

    def test_should_return_tokens_when_user_found_by_google_id(
        self,
        mock_oauth_provider: MagicMock,
        mock_google_auth_datasource: MagicMock,
        mock_token_manager: MagicMock,
        mock_token_revocation_store: MagicMock,
    ) -> None:
        """Test that tokens are returned when user is found by google_id."""
        existing_user = User(
            id="user-123",
            name="Existing",
            lastname="User",
            email=Email("existing@gmail.com"),
            password_hash=None,
            birthdate=date(2000, 1, 1),
            google_id="google-user-123",
        )
        mock_google_auth_datasource.get_user_by_google_id.return_value = existing_user

        use_case = HandleGoogleCallbackUseCase(
            oauth_provider=mock_oauth_provider,
            google_auth_datasource=mock_google_auth_datasource,
            token_manager=mock_token_manager,
            token_revocation_store=mock_token_revocation_store,
        )

        params = HandleGoogleCallbackParams(code="test-code")
        result = use_case.execute(params)

        assert result.access_token == "mock-access-token"
        mock_google_auth_datasource.create_google_user.assert_not_called()

    def test_should_raise_conflict_when_email_exists_with_password(
        self,
        mock_oauth_provider: MagicMock,
        mock_google_auth_datasource: MagicMock,
        mock_token_manager: MagicMock,
        mock_token_revocation_store: MagicMock,
    ) -> None:
        """Test that ConflictError is raised when email exists with password."""
        existing_user = User(
            id="user-123",
            name="Existing",
            lastname="User",
            email=Email("existing@gmail.com"),
            password_hash="$2b$12$hashedpassword",  # Has password
            birthdate=date(2000, 1, 1),
        )
        mock_google_auth_datasource.get_user_by_google_id.return_value = None
        mock_google_auth_datasource.get_user_by_email.return_value = existing_user

        use_case = HandleGoogleCallbackUseCase(
            oauth_provider=mock_oauth_provider,
            google_auth_datasource=mock_google_auth_datasource,
            token_manager=mock_token_manager,
            token_revocation_store=mock_token_revocation_store,
        )

        params = HandleGoogleCallbackParams(code="test-code")

        with pytest.raises(ConflictError) as exc_info:
            use_case.execute(params)

        assert "password account" in str(exc_info.value)

    def test_should_link_and_return_tokens_for_social_only_user(
        self,
        mock_oauth_provider: MagicMock,
        mock_google_auth_datasource: MagicMock,
        mock_token_manager: MagicMock,
        mock_token_revocation_store: MagicMock,
    ) -> None:
        """Test that social-only user (no password) is linked and logged in."""
        social_user = User(
            id="user-123",
            name="Social",
            lastname="User",
            email=Email("social@gmail.com"),
            password_hash=None,  # No password - social only
            birthdate=date(2000, 1, 1),
        )
        mock_google_auth_datasource.get_user_by_google_id.return_value = None
        mock_google_auth_datasource.get_user_by_email.return_value = social_user

        use_case = HandleGoogleCallbackUseCase(
            oauth_provider=mock_oauth_provider,
            google_auth_datasource=mock_google_auth_datasource,
            token_manager=mock_token_manager,
            token_revocation_store=mock_token_revocation_store,
        )

        params = HandleGoogleCallbackParams(code="test-code")
        result = use_case.execute(params)

        mock_google_auth_datasource.link_google_id.assert_called_once_with(
            "user-123", "google-user-123"
        )
        assert result.access_token == "mock-access-token"
