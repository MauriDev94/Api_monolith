"""Tests for GoogleAuthRepository."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import ConflictError
from app.features.auth.infrastructure.repositories.google_auth_repository import (
    GoogleAuthRepository,
)
from app.features.users.domain.entities.user import User
from app.features.users.infrastructure.repositories.user_provider_repository import (
    UserProviderRepository,
)


# Tipo de test: Integration
def test_should_create_google_user_and_fetch_by_google_id(db_session: Session) -> None:
    """Valida que crear usuario Google y recuperarlo por google_id."""
    repository = GoogleAuthRepository(user_provider=UserProviderRepository(session=db_session))
    google_account = User.create_from_google(
        google_id="google-123",
        email="googleuser@gmail.com",
        name="Google",
        lastname="User",
        google_email_verified=True,
    )

    created_user = repository.create_google_user(google_account)
    found_by_google_id = repository.get_user_by_google_id("google-123")
    found_by_email = repository.get_user_by_email("googleuser@gmail.com")

    assert created_user.id is not None
    assert created_user.google_id == "google-123"
    assert created_user.email.value == "googleuser@gmail.com"
    assert created_user.password_hash is None  # Google users don't have password
    assert found_by_google_id is not None
    assert found_by_google_id.id == created_user.id
    assert found_by_email is not None
    assert found_by_email.id == created_user.id


# Tipo de test: Integration
def test_should_create_google_user_with_google_email_verified_flag(db_session: Session) -> None:
    """Valida que se persiste el flag google_email_verified."""
    repository = GoogleAuthRepository(user_provider=UserProviderRepository(session=db_session))
    google_account = User.create_from_google(
        google_id="google-456",
        email="verified@gmail.com",
        name="Test",
        lastname="User",
        google_email_verified=True,
    )

    repository.create_google_user(google_account)
    found_user = repository.get_user_by_google_id("google-456")

    assert found_user is not None
    assert found_user.google_email_verified is True


# Tipo de test: Integration
def test_should_link_google_id_to_existing_user(db_session: Session) -> None:
    """Valida que link_google_id asocia google_id a un usuario existente."""
    repository = GoogleAuthRepository(user_provider=UserProviderRepository(session=db_session))
    google_account = User.create_from_google(
        google_id="google-temp",
        email="temp@gmail.com",
        name="Temp",
        lastname="User",
    )
    created_user = repository.create_google_user(google_account)

    # Clear google_id (simulating user created without it)
    repository.link_google_id(user_id=created_user.id or "", google_id="google-final")

    linked_user = repository.get_user_by_id(created_user.id or "")
    assert linked_user is not None
    assert linked_user.google_id == "google-final"


# Tipo de test: Integration
def test_should_return_none_when_user_not_found_by_google_id(db_session: Session) -> None:
    """Valida que retorna None cuando usuario no existe por google_id."""
    repository = GoogleAuthRepository(user_provider=UserProviderRepository(session=db_session))

    found = repository.get_user_by_google_id("non-existent-google-id")

    assert found is None


# Tipo de test: Integration
def test_should_raise_conflict_when_google_id_already_registered(db_session: Session) -> None:
    """Valida que lanza ConflictError cuando google_id ya está registrado."""
    repository = GoogleAuthRepository(user_provider=UserProviderRepository(session=db_session))
    google_account = User.create_from_google(
        google_id="duplicate-google-id",
        email="first@gmail.com",
        name="First",
        lastname="User",
    )
    repository.create_google_user(google_account)

    duplicate_account = User.create_from_google(
        google_id="duplicate-google-id",
        email="second@gmail.com",
        name="Second",
        lastname="User",
    )

    with pytest.raises(ConflictError):
        repository.create_google_user(duplicate_account)


# Tipo de test: Integration
def test_should_return_none_when_user_does_not_exist_by_id(db_session: Session) -> None:
    """Valida que retorna None cuando usuario no existe por id."""
    repository = GoogleAuthRepository(user_provider=UserProviderRepository(session=db_session))

    found = repository.get_user_by_id("non-existent-id")

    assert found is None
