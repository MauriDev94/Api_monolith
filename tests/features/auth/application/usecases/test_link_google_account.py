"""Tests for LinkGoogleAccountUseCase."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.core.exceptions.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.features.auth.application.contracts.google_auth_datasource import GoogleAuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.usecases.link_google_account import (
    LinkGoogleAccountParams,
    LinkGoogleAccountUseCase,
)
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


class TestLinkGoogleAccountUseCase:
    """Unit tests for LinkGoogleAccountUseCase."""

    @pytest.fixture
    def mock_google_auth_datasource(self) -> MagicMock:
        """Create a mock Google auth datasource."""
        datasource = MagicMock(spec=GoogleAuthDatasource)
        return datasource

    @pytest.fixture
    def mock_password_manager(self) -> MagicMock:
        """Create a mock password manager."""
        manager = MagicMock(spec=PasswordManager)
        manager.verify_password.return_value = True
        return manager

    @pytest.fixture
    def use_case(
        self,
        mock_google_auth_datasource: MagicMock,
        mock_password_manager: MagicMock,
    ) -> LinkGoogleAccountUseCase:
        """Create the use case with mocked dependencies."""
        return LinkGoogleAccountUseCase(
            google_auth_datasource=mock_google_auth_datasource,
            password_manager=mock_password_manager,
        )

    def test_should_link_google_account_when_password_is_valid(
        self,
        use_case: LinkGoogleAccountUseCase,
        mock_google_auth_datasource: MagicMock,
    ) -> None:
        """Test successful linking with valid password."""
        user = User(
            id="user-123",
            name="Test",
            lastname="User",
            email=Email("test@gmail.com"),
            password_hash="$2b$12$hashedpassword",
            birthdate=date(2000, 1, 1),
        )
        mock_google_auth_datasource.get_user_by_id.return_value = user

        params = LinkGoogleAccountParams(
            user_id="user-123",
            google_id="google-id-456",
            password="correct-password",
        )
        result = use_case.execute(params)

        assert result.success is True
        assert "linked successfully" in result.message
        mock_google_auth_datasource.link_google_id.assert_called_once_with(
            "user-123", "google-id-456"
        )

    def test_should_raise_not_found_when_user_does_not_exist(
        self,
        use_case: LinkGoogleAccountUseCase,
        mock_google_auth_datasource: MagicMock,
    ) -> None:
        """Test that NotFoundError is raised when user doesn't exist."""
        mock_google_auth_datasource.get_user_by_id.return_value = None

        params = LinkGoogleAccountParams(
            user_id="non-existent-user",
            google_id="google-id-456",
            password="password",
        )

        with pytest.raises(NotFoundError):
            use_case.execute(params)

    def test_should_raise_unauthorized_when_password_is_invalid(
        self,
        use_case: LinkGoogleAccountUseCase,
        mock_google_auth_datasource: MagicMock,
        mock_password_manager: MagicMock,
    ) -> None:
        """Test that UnauthorizedError is raised for invalid password."""
        user = User(
            id="user-123",
            name="Test",
            lastname="User",
            email=Email("test@gmail.com"),
            password_hash="$2b$12$hashedpassword",
            birthdate=date(2000, 1, 1),
        )
        mock_google_auth_datasource.get_user_by_id.return_value = user
        mock_password_manager.verify_password.return_value = False

        params = LinkGoogleAccountParams(
            user_id="user-123",
            google_id="google-id-456",
            password="wrong-password",
        )

        with pytest.raises(UnauthorizedError) as exc_info:
            use_case.execute(params)

        assert "Invalid password" in str(exc_info.value)

    def test_should_raise_conflict_when_user_already_has_google_linked(
        self,
        use_case: LinkGoogleAccountUseCase,
        mock_google_auth_datasource: MagicMock,
    ) -> None:
        """Test that ConflictError is raised if user already has google_id."""
        user = User(
            id="user-123",
            name="Test",
            lastname="User",
            email=Email("test@gmail.com"),
            password_hash="$2b$12$hashedpassword",
            birthdate=date(2000, 1, 1),
            google_id="already-linked-google-id",
        )
        mock_google_auth_datasource.get_user_by_id.return_value = user

        params = LinkGoogleAccountParams(
            user_id="user-123",
            google_id="new-google-id",
            password="correct-password",
        )

        with pytest.raises(ConflictError) as exc_info:
            use_case.execute(params)

        assert "already linked" in str(exc_info.value)

    def test_should_raise_unauthorized_when_user_has_no_password(
        self,
        use_case: LinkGoogleAccountUseCase,
        mock_google_auth_datasource: MagicMock,
    ) -> None:
        """Test that UnauthorizedError is raised for user without password."""
        user = User(
            id="user-123",
            name="Test",
            lastname="User",
            email=Email("test@gmail.com"),
            password_hash=None,  # No password
            birthdate=date(2000, 1, 1),
        )
        mock_google_auth_datasource.get_user_by_id.return_value = user

        params = LinkGoogleAccountParams(
            user_id="user-123",
            google_id="google-id-456",
            password="any-password",
        )

        with pytest.raises(UnauthorizedError) as exc_info:
            use_case.execute(params)

        assert "no password" in str(exc_info.value)
