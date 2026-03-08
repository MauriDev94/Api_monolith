from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import ResourceConflictException, ResourceNotFoundException
from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.auth.infrastructure.repositories.auth_repository import AuthRepository
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email
from app.features.users.infrastructure.repositories.user_repository import UserRepository


def _seed_user(
    session: Session,
    *,
    name: str,
    lastname: str,
    email: str,
) -> str:
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


# Tipo de test: Integration
def test_should_return_all_users(db_session: Session) -> None:
    """Valida que el repositorio retorna todos los usuarios persistidos."""
    repository = UserRepository(session=db_session)
    _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")
    _seed_user(db_session, name="Ana", lastname="Lopez", email="ana@mail.com")

    users = repository.get_all_users()

    assert len(users) == 2
    emails = {user.email.value for user in users}
    assert emails == {"mauri@mail.com", "ana@mail.com"}


# Tipo de test: Integration
def test_should_get_user_by_id(db_session: Session) -> None:
    """Valida que el repositorio obtiene un usuario por id."""
    repository = UserRepository(session=db_session)
    user_id = _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")

    user = repository.get_user_by_id(user_id)

    assert user is not None
    assert user.id == user_id
    assert user.email.value == "mauri@mail.com"


# Tipo de test: Integration
def test_should_report_email_registered_with_exclusion(db_session: Session) -> None:
    """Valida que la verificación de email respeta exclusión por user_id."""
    repository = UserRepository(session=db_session)
    user_id = _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")

    assert repository.is_email_registered("mauri@mail.com") is True
    assert repository.is_email_registered("mauri@mail.com", exclude_user_id=user_id) is False


# Tipo de test: Integration
def test_should_update_user_persisting_mutable_state(db_session: Session) -> None:
    """Valida que update persiste perfil y email desde la entidad mutable."""
    repository = UserRepository(session=db_session)
    user_id = _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")
    user = repository.get_user_by_id(user_id)
    assert user is not None

    user.change_name("Mauricio")
    user.change_lastname("Salas")
    user.change_birthdate(date(1999, 1, 1))
    user.change_email("mauricio@mail.com")

    updated_user = repository.update(user)

    assert updated_user.id == user_id
    assert updated_user.name == "Mauricio"
    assert updated_user.lastname == "Salas"
    assert updated_user.birthdate == date(1999, 1, 1)
    assert updated_user.email.value == "mauricio@mail.com"


# Tipo de test: Integration
def test_should_raise_not_found_when_updating_missing_user(db_session: Session) -> None:
    """Valida que update lanza not-found para usuario inexistente."""
    repository = UserRepository(session=db_session)

    missing_user = User(
        id="missing-id",
        name="Mauricio",
        lastname="Salinas",
        email=Email("mauricio@mail.com"),
        password_hash="hashed-password",
        birthdate=date(1999, 1, 1),
    )

    with pytest.raises(ResourceNotFoundException, match="user not found"):
        repository.update(missing_user)


# Tipo de test: Integration
def test_should_raise_conflict_when_updating_to_existing_email(db_session: Session) -> None:
    """Valida que update traduce conflicto al persistir email duplicado."""
    repository = UserRepository(session=db_session)
    first_user_id = _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")
    _seed_user(db_session, name="Ana", lastname="Lopez", email="ana@mail.com")

    first_user = repository.get_user_by_id(first_user_id)
    assert first_user is not None
    first_user.change_email("ana@mail.com")

    with pytest.raises(ResourceConflictException, match="email already registered"):
        repository.update(first_user)


# Tipo de test: Integration
def test_should_delete_existing_user(db_session: Session) -> None:
    """Valida que delete elimina usuario y mantiene contrato idempotente."""
    repository = UserRepository(session=db_session)
    user_id = _seed_user(db_session, name="Mauri", lastname="Salinas", email="mauri@mail.com")

    result = repository.delete(user_id)

    assert result is None
    assert repository.get_user_by_id(user_id) is None
