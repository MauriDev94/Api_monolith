from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.providers.db import get_db_session
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.usecases.delete_user_use_case import DeleteUser
from app.features.users.application.usecases.get_all_users_use_case import GetAllUsers
from app.features.users.application.usecases.get_user_by_id_use_case import GetUserById
from app.features.users.application.usecases.update_user_use_case import UpdateUser
from app.features.users.infrastructure.repositories.user_repository import UserRepository


def get_user_repository(db_session: Annotated[Session, Depends(get_db_session)]) -> UserDatasource:
    return UserRepository(session=db_session)


def get_get_all_users_use_case(
    user_datasource: Annotated[UserDatasource, Depends(get_user_repository)],
) -> GetAllUsers:
    return GetAllUsers(user_datasource=user_datasource)


def get_get_user_by_id_use_case(
    user_datasource: Annotated[UserDatasource, Depends(get_user_repository)],
) -> GetUserById:
    return GetUserById(user_datasource=user_datasource)


def get_update_user_use_case(
    user_datasource: Annotated[UserDatasource, Depends(get_user_repository)],
) -> UpdateUser:
    return UpdateUser(user_datasource=user_datasource)


def get_delete_user_use_case(
    user_datasource: Annotated[UserDatasource, Depends(get_user_repository)],
) -> DeleteUser:
    return DeleteUser(user_datasource=user_datasource)
