from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import ResourceConflictException, ResourceNotFoundException
from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.auth.infrastructure.repositories.auth_repository import AuthRepository
from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.infrastructure.repositories.user_repository import UserRepository


def _seed_user(
    session: Session,
    *,
    name: str,
    lastname: str,
    email: str,
) -> str:
    # Reuses auth repository so persisted users mimic real registration data.
    auth_repository = AuthRepository(session=session)
    user = auth_repository.register_user(
        params=RegisterUserParams(
            name=name,
            lastname=lastname,
            email=email,
            password="plain1234",
            birthdate=date(2000, 1, 1),
        ),
        password_hash="hashed-password",
    )
    return user.id or ""


# Verifies list operation returns all persisted users.
# Tipo de test: Integration
def test_should_return_all_users(db_session: Session) -> None:
    """Valida que retorna todos usuarios."""
    repository = UserRepository(session=db_session)
    _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")
    _seed_user(db_session, name="Ana", lastname="Lopez", email="ana@mail.com")

    users = repository.get_all_users()

    assert len(users) == 2
    emails = {user.email.value for user in users}
    assert emails == {"mauri@mail.com", "ana@mail.com"}


# Confirms direct lookup by primary key maps ORM model to domain entity.
# Tipo de test: Integration
def test_should_get_user_by_id(db_session: Session) -> None:
    """Valida que obtener un usuario por id."""
    repository = UserRepository(session=db_session)
    user_id = _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")

    user = repository.get_user_by_id(user_id)

    assert user is not None
    assert user.id == user_id
    assert user.email.value == "mauri@mail.com"


# Checks update persistence and returned entity values.
# Tipo de test: Integration
def test_should_update_user(db_session: Session) -> None:
    """Valida que actualizar usuario."""
    repository = UserRepository(session=db_session)
    user_id = _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")

    updated_user = repository.update_user(
        UpdateUserParams(
            id=user_id,
            name="Mauricio",
            lastname="Salinas",
            email="mauricio@mail.com",
            birthdate=date(1999, 1, 1),
        )
    )

    assert updated_user.id == user_id
    assert updated_user.name == "Mauricio"
    assert updated_user.email.value == "mauricio@mail.com"


# Protects contract: updating non-existing user must raise not-found.
# Tipo de test: Integration
def test_should_raise_not_found_when_updating_missing_user(db_session: Session) -> None:
    """Valida que lanza un error de no encontrado cuando actualizar faltante usuario."""
    repository = UserRepository(session=db_session)

    with pytest.raises(ResourceNotFoundException, match="user not found"):
        repository.update_user(
            UpdateUserParams(
                id="missing-id",
                name="Mauricio",
                lastname="Salinas",
                email="mauricio@mail.com",
                birthdate=date(1999, 1, 1),
            )
        )


# Ensures DB unique constraint is translated to ResourceConflictException.
# Tipo de test: Integration
def test_should_raise_conflict_when_updating_to_existing_email(db_session: Session) -> None:
    """Valida que lanza conflicto cuando actualizar existente email."""
    repository = UserRepository(session=db_session)
    first_user_id = _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")
    _seed_user(db_session, name="Ana", lastname="Lopez", email="ana@mail.com")

    with pytest.raises(ResourceConflictException, match="email already registered"):
        repository.update_user(
            UpdateUserParams(
                id=first_user_id,
                name="Mauri",
                lastname="Salinas",
                email="ana@mail.com",
                birthdate=date(2000, 1, 1),
            )
        )


# Verifies delete operation is effective and idempotent contract remains intact.
# Tipo de test: Integration
def test_should_delete_existing_user(db_session: Session) -> None:
    """Valida que eliminar existente usuario."""
    repository = UserRepository(session=db_session)
    user_id = _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")

    result = repository.delete_user(user_id)

    assert result is None
    assert repository.get_user_by_id(user_id) is None
