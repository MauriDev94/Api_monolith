from datetime import date
from unittest.mock import Mock

import pytest

from app.core.exceptions.exceptions import ConflictError, NotFoundError
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.delete_user_params import DeleteUserParams
from app.features.users.application.dto.get_user_by_id_params import GetUserByIdParams
from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.application.usecases.delete_user_use_case import DeleteUserUseCase
from app.features.users.application.usecases.get_user_by_id_use_case import GetUserByIdUseCase
from app.features.users.application.usecases.update_user_use_case import UpdateUserUseCase
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


def make_user() -> User:
    return User(
        id="user-1",
        name="Mauri",
        lastname="Salinas",
        email=Email("mauri@mail.com"),
        password_hash="hashed-password",
        birthdate=date(2000, 1, 1),
    )


# Tipo de test: Unit
def test_should_raise_not_found_when_get_user_by_id_returns_none() -> None:
    """Valida que obtener usuario por id lanza not-found cuando no existe."""
    datasource = Mock(spec=UserDatasource)
    datasource.get_user_by_id.return_value = None
    use_case = GetUserByIdUseCase(user_datasource=datasource)

    with pytest.raises(NotFoundError, match="user not found"):
        use_case.execute(GetUserByIdParams(user_id="missing"))


# Tipo de test: Unit
def test_should_return_user_when_get_user_by_id_finds_entity() -> None:
    """Valida que obtener usuario por id retorna entidad cuando existe."""
    datasource = Mock(spec=UserDatasource)
    expected_user = make_user()
    datasource.get_user_by_id.return_value = expected_user
    use_case = GetUserByIdUseCase(user_datasource=datasource)

    result = use_case.execute(GetUserByIdParams(user_id="user-1"))

    datasource.get_user_by_id.assert_called_once_with("user-1")
    assert result == expected_user


# Tipo de test: Unit
def test_should_update_profile_and_email_and_persist_once() -> None:
    """Valida que update muta perfil/email y persiste una sola vez."""
    datasource = Mock(spec=UserDatasource)
    existing_user = make_user()
    datasource.get_user_by_id.return_value = existing_user
    datasource.is_email_registered.return_value = False
    datasource.update.return_value = existing_user
    use_case = UpdateUserUseCase(user_datasource=datasource)

    params = UpdateUserParams(
        user_id="user-1",
        name="Mauricio",
        lastname="Salas",
        email="new@mail.com",
        birthdate=date(1999, 1, 1),
    )

    result = use_case.execute(params)

    datasource.get_user_by_id.assert_called_once_with("user-1")
    datasource.is_email_registered.assert_called_once_with(
        Email("new@mail.com"), exclude_user_id="user-1"
    )
    datasource.update.assert_called_once()
    persisted_user = datasource.update.call_args.args[0]
    assert persisted_user.name == "Mauricio"
    assert persisted_user.lastname == "Salas"
    assert persisted_user.birthdate == date(1999, 1, 1)
    assert persisted_user.email.value == "new@mail.com"
    assert result == existing_user


# Tipo de test: Unit
def test_should_skip_email_check_when_email_is_unchanged_after_normalization() -> None:
    """Valida que no verifica disponibilidad si el email normalizado no cambia."""
    datasource = Mock(spec=UserDatasource)
    existing_user = make_user()
    datasource.get_user_by_id.return_value = existing_user
    datasource.update.return_value = existing_user
    use_case = UpdateUserUseCase(user_datasource=datasource)

    params = UpdateUserParams(
        user_id="user-1",
        name="Mauricio",
        lastname="Salas",
        email="Mauri@Mail.com",
        birthdate=date(1999, 1, 1),
    )

    result = use_case.execute(params)

    datasource.is_email_registered.assert_not_called()
    datasource.update.assert_called_once()
    assert result == existing_user


# Tipo de test: Unit
def test_should_raise_conflict_when_new_email_is_already_registered() -> None:
    """Valida que update lanza conflicto si el nuevo email ya está registrado."""
    datasource = Mock(spec=UserDatasource)
    datasource.get_user_by_id.return_value = make_user()
    datasource.is_email_registered.return_value = True
    use_case = UpdateUserUseCase(user_datasource=datasource)

    with pytest.raises(ConflictError, match="email already registered"):
        use_case.execute(
            UpdateUserParams(
                user_id="user-1",
                name="Mauricio",
                lastname="Salas",
                email="ana@mail.com",
                birthdate=date(1999, 1, 1),
            )
        )

    datasource.update.assert_not_called()


# Tipo de test: Unit
def test_should_raise_not_found_when_updating_missing_user() -> None:
    """Valida que update lanza not-found cuando el usuario no existe."""
    datasource = Mock(spec=UserDatasource)
    datasource.get_user_by_id.return_value = None
    use_case = UpdateUserUseCase(user_datasource=datasource)

    with pytest.raises(NotFoundError, match="user not found"):
        use_case.execute(
            UpdateUserParams(
                user_id="missing",
                name="Mauricio",
                lastname="Salas",
                email="new@mail.com",
                birthdate=date(1999, 1, 1),
            )
        )


# Tipo de test: Unit
def test_should_delegate_delete_user_to_datasource() -> None:
    """Valida que delete delega la eliminación al datasource."""
    datasource = Mock(spec=UserDatasource)
    use_case = DeleteUserUseCase(user_datasource=datasource)

    use_case.execute(DeleteUserParams(user_id="user-1"))

    datasource.delete.assert_called_once_with("user-1")
