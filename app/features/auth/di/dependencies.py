from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config.env_config import EnvConfig
from app.core.providers.db import get_db_session
from app.core.providers.env_config import get_env_config
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.usecases.get_current_user_use_case import GetCurrentUser
from app.features.auth.application.usecases.login_user_use_case import LoginUser
from app.features.auth.application.usecases.refresh_access_token_use_case import RefreshAccessToken
from app.features.auth.application.usecases.register_user_use_case import RegisterUser
from app.features.auth.infrastructure.managers.jwt_token_manager import JwtTokenManager
from app.features.auth.infrastructure.managers.password_manager_impl import PasswordManagerImpl
from app.features.auth.infrastructure.repositories.auth_repository import AuthRepository


def get_auth_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> AuthDatasource:
    return AuthRepository(session=db_session)


def get_password_manager() -> PasswordManager:
    return PasswordManagerImpl()


def get_token_manager(
    env_config: Annotated[EnvConfig, Depends(get_env_config)],
) -> TokenManager:
    return JwtTokenManager(secret_key=env_config.jwt_secret_key)


def get_register_user_use_case(
    auth_datasource: Annotated[AuthDatasource, Depends(get_auth_repository)],
    password_manager: Annotated[PasswordManager, Depends(get_password_manager)],
) -> RegisterUser:
    return RegisterUser(auth_datasource=auth_datasource, password_manager=password_manager)


def get_login_user_use_case(
    auth_datasource: Annotated[AuthDatasource, Depends(get_auth_repository)],
    password_manager: Annotated[PasswordManager, Depends(get_password_manager)],
    token_manager: Annotated[TokenManager, Depends(get_token_manager)],
) -> LoginUser:
    return LoginUser(
        auth_datasource=auth_datasource,
        password_manager=password_manager,
        token_manager=token_manager,
    )


def get_refresh_access_token_use_case(
    token_manager: Annotated[TokenManager, Depends(get_token_manager)],
) -> RefreshAccessToken:
    return RefreshAccessToken(token_manager=token_manager)


def get_current_user_use_case(
    auth_datasource: Annotated[AuthDatasource, Depends(get_auth_repository)],
    token_manager: Annotated[TokenManager, Depends(get_token_manager)],
) -> GetCurrentUser:
    return GetCurrentUser(auth_datasource=auth_datasource, token_manager=token_manager)
