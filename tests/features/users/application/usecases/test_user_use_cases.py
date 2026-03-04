from datetime import date
from unittest.mock import Mock

import pytest

from app.core.exceptions.exceptions import ResourceNotFoundException
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.delete_user_params import DeleteUserParams
from app.features.users.application.dto.get_user_by_id_params import GetUserByIdParams
from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.application.usecases.delete_user_use_case import DeleteUser
from app.features.users.application.usecases.get_all_users_use_case import GetAllUsers
from app.features.users.application.usecases.get_user_by_id_use_case import GetUserById
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
    """Valida que delegate obtener todos usuarios a fuente de datos."""
    datasource = Mock(spec=UserDatasource)
    expected_users = [make_user()]
    datasource.get_all_users.return_value = expected_users
    use_case = GetAllUsers(user_datasource=datasource)

    result = use_case.execute()

    datasource.get_all_users.assert_called_once_with()
    assert result == expected_users


# Tipo de test: Unit
def test_should_raise_not_found_when_get_user_by_id_returns_none() -> None:
    """Valida que lanza no encontrado cuando obtener usuario por id retorna ninguno."""
    datasource = Mock(spec=UserDatasource)
    datasource.get_user_by_id.return_value = None
    use_case = GetUserById(user_datasource=datasource)

    with pytest.raises(ResourceNotFoundException, match="user not found"):
        use_case.execute(GetUserByIdParams(user_id="missing"))


# Tipo de test: Unit
def test_should_return_user_when_get_user_by_id_finds_entity() -> None:
    """Valida que retorna usuario cuando obtiene usuario por id finds entidad."""
    datasource = Mock(spec=UserDatasource)
    expected_user = make_user()
    datasource.get_user_by_id.return_value = expected_user
    use_case = GetUserById(user_datasource=datasource)

    result = use_case.execute(GetUserByIdParams(user_id="user-1"))

    datasource.get_user_by_id.assert_called_once_with("user-1")
    assert result == expected_user


# Tipo de test: Unit
def test_should_delegate_update_user_to_datasource() -> None:
    """Valida que delegate actualize usuario a fuente de datos."""
    datasource = Mock(spec=UserDatasource)
    expected_user = make_user()
    datasource.update_user.return_value = expected_user
    use_case = UpdateUser(user_datasource=datasource)
    params = UpdateUserParams(
        id="user-1",
        name="Mauricio",
        lastname="Salinas",
        email="mauricio@mail.com",
        birthdate=date(2000, 1, 1),
    )

    result = use_case.execute(params)

    datasource.update_user.assert_called_once_with(params)
    assert result == expected_user


# Tipo de test: Unit
def test_should_delegate_delete_user_to_datasource() -> None:
    """Valida que delegate elimine usuario a fuente de datos."""
    datasource = Mock(spec=UserDatasource)
    use_case = DeleteUser(user_datasource=datasource)

    result = use_case.execute(DeleteUserParams(user_id="user-1"))

    datasource.delete_user.assert_called_once_with("user-1")
    assert result is None
