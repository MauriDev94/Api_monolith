from datetime import date
from unittest.mock import Mock

import pytest

from app.core.exceptions.exceptions import ResourceConflictException, ResourceNotFoundException
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.change_user_email_params import ChangeUserEmailParams
from app.features.users.application.dto.delete_user_params import DeleteUserParams
from app.features.users.application.dto.get_user_by_id_params import GetUserByIdParams
from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.application.dto.update_user_profile_params import UpdateUserProfileParams
from app.features.users.application.usecases.change_user_email_use_case import ChangeUserEmail
from app.features.users.application.usecases.delete_user_use_case import DeleteUser
from app.features.users.application.usecases.get_all_users_use_case import GetAllUsers
from app.features.users.application.usecases.get_user_by_id_use_case import GetUserById
from app.features.users.application.usecases.update_user_profile_use_case import UpdateUserProfile
from app.features.users.application.usecases.update_user_use_case import UpdateUser
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
def test_should_delegate_get_all_users_to_datasource() -> None:
    """Valida que el caso de uso delega el listado de usuarios al datasource."""
    datasource = Mock(spec=UserDatasource)
    expected_users = [make_user()]
    datasource.get_all_users.return_value = expected_users
    use_case = GetAllUsers(user_datasource=datasource)

    result = use_case.execute()

    datasource.get_all_users.assert_called_once_with()
    assert result == expected_users


# Tipo de test: Unit
def test_should_raise_not_found_when_get_user_by_id_returns_none() -> None:
    """Valida que obtener usuario por id lanza not-found cuando no existe."""
    datasource = Mock(spec=UserDatasource)
    datasource.get_user_by_id.return_value = None
    use_case = GetUserById(user_datasource=datasource)

    with pytest.raises(ResourceNotFoundException, match="user not found"):
        use_case.execute(GetUserByIdParams(user_id="missing"))


# Tipo de test: Unit
def test_should_return_user_when_get_user_by_id_finds_entity() -> None:
    """Valida que obtener usuario por id retorna entidad cuando existe."""
    datasource = Mock(spec=UserDatasource)
    expected_user = make_user()
    datasource.get_user_by_id.return_value = expected_user
    use_case = GetUserById(user_datasource=datasource)

    result = use_case.execute(GetUserByIdParams(user_id="user-1"))

    datasource.get_user_by_id.assert_called_once_with("user-1")
    assert result == expected_user


# Tipo de test: Unit
def test_should_mutate_and_persist_profile_fields_when_update_profile_is_valid() -> None:
    """Valida que update profile aplica cambios de nombre, apellido y fecha y los persiste."""
    datasource = Mock(spec=UserDatasource)
    existing_user = make_user()
    datasource.get_user_by_id.return_value = existing_user
    datasource.update_user_profile.return_value = existing_user
    use_case = UpdateUserProfile(user_datasource=datasource)

    result = use_case.execute(
        UpdateUserProfileParams(
            id="user-1",
            name="Mauricio",
            lastname="Salas",
            birthdate=date(1999, 1, 1),
        )
    )

    datasource.get_user_by_id.assert_called_once_with("user-1")
    datasource.update_user_profile.assert_called_once()
    persisted_user = datasource.update_user_profile.call_args.args[0]
    assert persisted_user.name == "Mauricio"
    assert persisted_user.lastname == "Salas"
    assert persisted_user.birthdate == date(1999, 1, 1)
    assert result == existing_user


# Tipo de test: Unit
def test_should_raise_not_found_when_updating_profile_of_missing_user() -> None:
    """Valida que update profile lanza not-found cuando el usuario no existe."""
    datasource = Mock(spec=UserDatasource)
    datasource.get_user_by_id.return_value = None
    use_case = UpdateUserProfile(user_datasource=datasource)

    with pytest.raises(ResourceNotFoundException, match="user not found"):
        use_case.execute(
            UpdateUserProfileParams(
                id="missing",
                name="Mauricio",
                lastname="Salas",
                birthdate=date(1999, 1, 1),
            )
        )


# Tipo de test: Unit
def test_should_change_email_and_persist_when_change_email_is_valid() -> None:
    """Valida que change email verifica disponibilidad, muta email y persiste."""
    datasource = Mock(spec=UserDatasource)
    existing_user = make_user()
    datasource.get_user_by_id.return_value = existing_user
    datasource.is_email_registered.return_value = False
    datasource.update_user_email.return_value = existing_user
    use_case = ChangeUserEmail(user_datasource=datasource)

    result = use_case.execute(ChangeUserEmailParams(id="user-1", email="new@mail.com"))

    datasource.get_user_by_id.assert_called_once_with("user-1")
    datasource.is_email_registered.assert_called_once_with("new@mail.com", exclude_user_id="user-1")
    datasource.update_user_email.assert_called_once()
    persisted_user = datasource.update_user_email.call_args.args[0]
    assert persisted_user.email.value == "new@mail.com"
    assert result == existing_user


# Tipo de test: Unit
def test_should_raise_conflict_when_changing_to_taken_email() -> None:
    """Valida que change email lanza conflicto cuando el email ya existe."""
    datasource = Mock(spec=UserDatasource)
    datasource.get_user_by_id.return_value = make_user()
    datasource.is_email_registered.return_value = True
    use_case = ChangeUserEmail(user_datasource=datasource)

    with pytest.raises(ResourceConflictException, match="email already registered"):
        use_case.execute(ChangeUserEmailParams(id="user-1", email="ana@mail.com"))

    datasource.update_user_email.assert_not_called()


# Tipo de test: Unit
def test_should_raise_not_found_when_changing_email_of_missing_user() -> None:
    """Valida que change email lanza not-found cuando el usuario no existe."""
    datasource = Mock(spec=UserDatasource)
    datasource.get_user_by_id.return_value = None
    use_case = ChangeUserEmail(user_datasource=datasource)

    with pytest.raises(ResourceNotFoundException, match="user not found"):
        use_case.execute(ChangeUserEmailParams(id="missing", email="new@mail.com"))


# Tipo de test: Unit
def test_should_orchestrate_profile_and_email_when_email_changed() -> None:
    """Valida que update user ejecuta profile y luego change email cuando el email cambia."""
    datasource = Mock(spec=UserDatasource)
    profile_use_case = Mock()
    email_use_case = Mock()

    profile_user = make_user()
    profile_user.email = Email("old@mail.com")
    final_user = make_user()
    final_user.email = Email("new@mail.com")

    profile_use_case.execute.return_value = profile_user
    email_use_case.execute.return_value = final_user

    use_case = UpdateUser(
        user_datasource=datasource,
        update_user_profile_use_case=profile_use_case,
        change_user_email_use_case=email_use_case,
    )

    params = UpdateUserParams(
        id="user-1",
        name="Mauricio",
        lastname="Salas",
        email="new@mail.com",
        birthdate=date(1999, 1, 1),
    )

    result = use_case.execute(params)

    profile_use_case.execute.assert_called_once()
    email_use_case.execute.assert_called_once()
    assert result == final_user


# Tipo de test: Unit
def test_should_skip_change_email_when_email_is_the_same() -> None:
    """Valida que update user no ejecuta change email cuando el email no cambia."""
    datasource = Mock(spec=UserDatasource)
    profile_use_case = Mock()
    email_use_case = Mock()

    profile_user = make_user()
    profile_user.email = Email("mauri@mail.com")
    profile_use_case.execute.return_value = profile_user

    use_case = UpdateUser(
        user_datasource=datasource,
        update_user_profile_use_case=profile_use_case,
        change_user_email_use_case=email_use_case,
    )

    params = UpdateUserParams(
        id="user-1",
        name="Mauricio",
        lastname="Salas",
        email="Mauri@Mail.com",
        birthdate=date(1999, 1, 1),
    )

    result = use_case.execute(params)

    profile_use_case.execute.assert_called_once()
    email_use_case.execute.assert_not_called()
    assert result == profile_user


# Tipo de test: Unit
def test_should_delegate_delete_user_to_datasource() -> None:
    """Valida que delete delega la eliminacion al datasource."""
    datasource = Mock(spec=UserDatasource)
    use_case = DeleteUser(user_datasource=datasource)

    result = use_case.execute(DeleteUserParams(user_id="user-1"))

    datasource.delete_user.assert_called_once_with("user-1")
    assert result is None
