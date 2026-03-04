from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import ResourceConflictException
from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.auth.infrastructure.repositories.auth_repository import AuthRepository


# Validates end-to-end persistence flow in auth repository: register + fetch by both lookup keys.
def test_should_register_user_and_fetch_by_email_and_id(db_session: Session) -> None:
    repository = AuthRepository(session=db_session)
    params = RegisterUserParams(
        name="Mauri",
        lastname="Salinas",
        email="mauri@mail.com",
        password="plain1234",
        birthdate=date(2000, 1, 1),
    )

    created_user = repository.register_user(params=params, password_hash="hashed-password")
    found_by_email = repository.get_user_by_email("mauri@mail.com")
    found_by_id = repository.get_user_by_id(created_user.id or "")

    assert created_user.id is not None
    assert created_user.email.value == "mauri@mail.com"
    assert found_by_email is not None
    assert found_by_email.id == created_user.id
    assert found_by_id is not None
    assert found_by_id.id == created_user.id


# Ensures missing users are handled safely with None instead of exceptions.
def test_should_return_none_when_user_does_not_exist(db_session: Session) -> None:
    repository = AuthRepository(session=db_session)

    found_by_email = repository.get_user_by_email("missing@mail.com")
    found_by_id = repository.get_user_by_id("missing-id")

    assert found_by_email is None
    assert found_by_id is None


# Confirms unique email constraint is translated into domain-level conflict exception.
def test_should_raise_conflict_when_registering_duplicate_email(db_session: Session) -> None:
    repository = AuthRepository(session=db_session)
    params = RegisterUserParams(
        name="Mauri",
        lastname="Salinas",
        email="mauri@mail.com",
        password="plain1234",
        birthdate=date(2000, 1, 1),
    )

    repository.register_user(params=params, password_hash="hashed-password")

    with pytest.raises(ResourceConflictException, match="email already registered"):
        repository.register_user(params=params, password_hash="another-hash")
