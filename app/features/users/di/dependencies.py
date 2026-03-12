from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.providers.db import get_db_session
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.usecases.delete_user_use_case import DeleteUserUseCase
from app.features.users.application.usecases.get_all_users_use_case import GetAllUsersUseCase
from app.features.users.application.usecases.get_user_by_id_use_case import GetUserByIdUseCase
from app.features.users.application.usecases.update_user_use_case import UpdateUserUseCase
from app.features.users.infrastructure.repositories.user_repository import UserRepository


def get_user_repository(db_session: Annotated[Session, Depends(get_db_session)]) -> UserDatasource:
    """Provide SQLAlchemy-backed datasource for user use cases."""
    return UserRepository(session=db_session)


def get_get_all_users_use_case(
    user_datasource: Annotated[UserDatasource, Depends(get_user_repository)],
) -> GetAllUsersUseCase:
    """Provide GetAllUsersUseCase use case."""
    return GetAllUsersUseCase(user_datasource=user_datasource)


def get_get_user_by_id_use_case(
    user_datasource: Annotated[UserDatasource, Depends(get_user_repository)],
) -> GetUserByIdUseCase:
    """Provide GetUserByIdUseCase use case."""
    return GetUserByIdUseCase(user_datasource=user_datasource)


def get_update_user_use_case(
    user_datasource: Annotated[UserDatasource, Depends(get_user_repository)],
) -> UpdateUserUseCase:
    """Provide UpdateUserUseCase use case."""
    return UpdateUserUseCase(user_datasource=user_datasource)


def get_delete_user_use_case(
    user_datasource: Annotated[UserDatasource, Depends(get_user_repository)],
) -> DeleteUserUseCase:
    """Provide DeleteUserUseCase use case."""
    return DeleteUserUseCase(user_datasource=user_datasource)
