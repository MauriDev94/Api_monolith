from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import ConflictError
from app.features.auth.infrastructure.repositories.auth_repository import AuthRepository
from app.features.users.domain.entities.user import User
from app.features.users.infrastructure.repositories.user_provider_repository import (
    UserProviderRepository,
)


# Validates end-to-end persistence flow in auth repository: register + fetch by both lookup keys.
# Tipo de test: Integration
def test_should_register_user_and_fetch_by_email_and_id(db_session: Session) -> None:
    """Valida que registrar usuario y recuperar por email y id."""
    repository = AuthRepository(user_provider=UserProviderRepository(session=db_session))
    new_account = User.create_new(
        name="Mauri",
        lastname="Salinas",
        email="mauri@mail.com",
        birthdate=date(2000, 1, 1),
        password_hash="hashed-password",
    )

    created_user = repository.register_user(new_account)
    found_by_email = repository.get_user_by_email("mauri@mail.com")
    found_by_id = repository.get_user_by_id(created_user.id or "")

    assert created_user.id is not None
    assert created_user.email.value == "mauri@mail.com"
    assert found_by_email is not None
    assert found_by_email.id == created_user.id
    assert found_by_id is not None
    assert found_by_id.id == created_user.id


# Tipo de test: Integration
def test_should_normalize_email_on_register_and_lookup(db_session: Session) -> None:
    """Valida que repositorio normaliza email al registrar y buscar."""
    repository = AuthRepository(user_provider=UserProviderRepository(session=db_session))
    new_account = User.create_new(
        name="Mauri",
        lastname="Salinas",
        email="  MAURI@MAIL.COM  ",
        birthdate=date(2000, 1, 1),
        password_hash="hashed-password",
    )

    created_user = repository.register_user(new_account)
    found_by_email = repository.get_user_by_email("  mauri@mail.com  ")

    assert created_user.email.value == "mauri@mail.com"
    assert found_by_email is not None
    assert found_by_email.id == created_user.id


# Ensures missing users are handled safely with None instead of exceptions.
# Tipo de test: Integration
def test_should_return_none_when_user_does_not_exist(db_session: Session) -> None:
    """Valida que retorna None cuando usuario no existe."""
    repository = AuthRepository(user_provider=UserProviderRepository(session=db_session))

    found_by_email = repository.get_user_by_email("missing@mail.com")
    found_by_id = repository.get_user_by_id("missing-id")

    assert found_by_email is None
    assert found_by_id is None


# Confirms unique email constraint is translated into domain-level conflict exception.
# Tipo de test: Integration
def test_should_raise_conflict_when_registering_duplicate_email(db_session: Session) -> None:
    """Valida que lanza conflicto cuando registrar duplicado email."""
    repository = AuthRepository(user_provider=UserProviderRepository(session=db_session))
    first_account = User.create_new(
        name="Mauri",
        lastname="Salinas",
        email="  MAURI@MAIL.COM  ",
        birthdate=date(2000, 1, 1),
        password_hash="hashed-password",
    )
    duplicate_account = User.create_new(
        name="Mauri",
        lastname="Salinas",
        email="mauri@mail.com",
        birthdate=date(2000, 1, 1),
        password_hash="hashed-password",
    )

    repository.register_user(first_account)

    with pytest.raises(ConflictError, match="email already registered"):
        repository.register_user(duplicate_account)


# Tipo de test: Integration
def test_should_update_password_hash_for_existing_user(db_session: Session) -> None:
    """Valida que update_password persiste el nuevo hash para un usuario existente."""
    repository = AuthRepository(user_provider=UserProviderRepository(session=db_session))
    new_account = User.create_new(
        name="Mauri",
        lastname="Salinas",
        email="mauri@mail.com",
        birthdate=date(2000, 1, 1),
        password_hash="hashed-password",
    )
    created_user = repository.register_user(new_account)

    repository.update_password(user_id=created_user.id or "", password_hash="new-hash")
    updated_user = repository.get_user_by_id(created_user.id or "")

    assert updated_user is not None
    assert updated_user.password_hash == "new-hash"


# Tipo de test: Integration
def test_should_ignore_update_password_when_user_does_not_exist(db_session: Session) -> None:
    """Valida que update_password no falla cuando el usuario no existe."""
    repository = AuthRepository(user_provider=UserProviderRepository(session=db_session))

    repository.update_password(user_id="missing-id", password_hash="new-hash")
