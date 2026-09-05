import os
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config.env_config import EnvConfig
from app.core.providers.db import get_db_session
from app.core.providers.env_config import get_env_config
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.email_sender import EmailSender
from app.features.auth.application.contracts.google_auth_datasource import GoogleAuthDatasource
from app.features.auth.application.contracts.oauth_provider import OAuthProvider
from app.features.auth.application.contracts.otp_datasource import OtpDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.rate_limiter import RateLimiter
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.usecases.change_password_with_otp_use_case import (
    ChangePasswordWithOtpUseCase,
)
from app.features.auth.application.usecases.get_current_user_use_case import GetCurrentUser
from app.features.auth.application.usecases.handle_google_callback import (
    HandleGoogleCallbackUseCase,
)
from app.features.auth.application.usecases.initiate_google_login import InitiateGoogleLoginUseCase
from app.features.auth.application.usecases.link_google_account import LinkGoogleAccountUseCase
from app.features.auth.application.usecases.login_user_use_case import LoginUser
from app.features.auth.application.usecases.refresh_access_token_use_case import RefreshAccessToken
from app.features.auth.application.usecases.register_user_use_case import RegisterUser
from app.features.auth.application.usecases.request_otp_use_case import RequestOtpUseCase
from app.features.auth.application.usecases.verify_otp_use_case import VerifyOtpUseCase
from app.features.auth.infrastructure.managers.jwt_token_manager import JwtTokenManager
from app.features.auth.infrastructure.managers.password_manager_impl import PasswordManagerImpl
from app.features.auth.infrastructure.providers.console_email_sender import ConsoleEmailSender
from app.features.auth.infrastructure.providers.google_oauth_provider import GoogleOAuthProviderImpl
from app.features.auth.infrastructure.providers.resend_email_sender import ResendEmailSender
from app.features.auth.infrastructure.repositories.auth_repository import AuthRepository
from app.features.auth.infrastructure.repositories.google_auth_repository import (
    GoogleAuthRepository,
)
from app.features.auth.infrastructure.repositories.otp_repository import OtpRepository
from app.features.auth.infrastructure.repositories.token_revocation_repository import (
    TokenRevocationRepository,
)
from app.features.auth.infrastructure.security.in_memory_rate_limiter import (
    InMemoryRateLimiter,
    NoOpRateLimiter,
)
from app.features.users.application.contracts.user_provider import UserProvider
from app.features.users.di.dependencies import get_user_provider

_rate_limiter = InMemoryRateLimiter()
_noop_rate_limiter = NoOpRateLimiter()


def get_auth_repository(
    user_provider: Annotated[UserProvider, Depends(get_user_provider)],
) -> AuthDatasource:
    """Provide auth datasource backed by the users port (no direct UserModel access)."""
    return AuthRepository(user_provider=user_provider)


def get_password_manager() -> PasswordManager:
    """Provide password hashing implementation."""
    return PasswordManagerImpl()


def get_token_manager(
    env_config: Annotated[EnvConfig, Depends(get_env_config)],
) -> TokenManager:
    """Provide JWT token manager using configured secret key."""
    return JwtTokenManager(secret_key=env_config.jwt_secret_key)


def get_token_revocation_store(
    db_session: Annotated[Session, Depends(get_db_session)],
) -> TokenRevocationStore:
    """Provide refresh token revocation store backed by SQLAlchemy."""
    return TokenRevocationRepository(session=db_session)


def get_otp_repository(
    db_session: Annotated[Session, Depends(get_db_session)],
    env_config: Annotated[EnvConfig, Depends(get_env_config)],
) -> OtpDatasource:
    """Provide OTP datasource implementation backed by SQLAlchemy."""
    return OtpRepository(session=db_session, secret_key=env_config.jwt_secret_key)


def get_email_sender(
    env_config: Annotated[EnvConfig, Depends(get_env_config)],
) -> EmailSender:
    """Provide Resend email sender or fallback to console sender."""
    if env_config.resend_api_key and env_config.resend_sender_email:
        return ResendEmailSender(
            api_key=env_config.resend_api_key,
            sender_email=env_config.resend_sender_email,
        )
    return ConsoleEmailSender()


def get_rate_limiter() -> RateLimiter:
    """Provide the shared rate limiter, or a no-op when rate limiting is disabled.

    RATE_LIMIT_ENABLED=false (p.ej. en tests) devuelve un limiter no-op para evitar
    acumulación de estado entre tests; los tests de rate limiting inyectan uno real.
    """
    if os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "false":
        return _noop_rate_limiter
    return _rate_limiter


def get_register_user_use_case(
    auth_datasource: Annotated[AuthDatasource, Depends(get_auth_repository)],
    password_manager: Annotated[PasswordManager, Depends(get_password_manager)],
) -> RegisterUser:
    """Provide RegisterUser use case with required dependencies."""
    return RegisterUser(auth_datasource=auth_datasource, password_manager=password_manager)


def get_login_user_use_case(
    auth_datasource: Annotated[AuthDatasource, Depends(get_auth_repository)],
    password_manager: Annotated[PasswordManager, Depends(get_password_manager)],
    token_manager: Annotated[TokenManager, Depends(get_token_manager)],
    token_revocation_store: Annotated[TokenRevocationStore, Depends(get_token_revocation_store)],
) -> LoginUser:
    """Provide LoginUser use case with required dependencies."""
    return LoginUser(
        auth_datasource=auth_datasource,
        password_manager=password_manager,
        token_manager=token_manager,
        token_revocation_store=token_revocation_store,
    )


def get_refresh_access_token_use_case(
    token_manager: Annotated[TokenManager, Depends(get_token_manager)],
    token_revocation_store: Annotated[TokenRevocationStore, Depends(get_token_revocation_store)],
) -> RefreshAccessToken:
    """Provide RefreshAccessToken use case."""
    return RefreshAccessToken(
        token_manager=token_manager,
        token_revocation_store=token_revocation_store,
    )


def get_current_user_use_case(
    auth_datasource: Annotated[AuthDatasource, Depends(get_auth_repository)],
    token_manager: Annotated[TokenManager, Depends(get_token_manager)],
) -> GetCurrentUser:
    """Provide GetCurrentUser use case."""
    return GetCurrentUser(auth_datasource=auth_datasource, token_manager=token_manager)


def get_request_otp_use_case(
    auth_datasource: Annotated[AuthDatasource, Depends(get_auth_repository)],
    otp_datasource: Annotated[OtpDatasource, Depends(get_otp_repository)],
    email_sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> RequestOtpUseCase:
    """Provide RequestOtpUseCase use case."""
    return RequestOtpUseCase(
        auth_datasource=auth_datasource,
        otp_datasource=otp_datasource,
        email_sender=email_sender,
    )


def get_verify_otp_use_case(
    otp_datasource: Annotated[OtpDatasource, Depends(get_otp_repository)],
) -> VerifyOtpUseCase:
    """Provide VerifyOtpUseCase use case."""
    return VerifyOtpUseCase(otp_datasource=otp_datasource)


def get_change_password_with_otp_use_case(
    auth_datasource: Annotated[AuthDatasource, Depends(get_auth_repository)],
    otp_datasource: Annotated[OtpDatasource, Depends(get_otp_repository)],
    password_manager: Annotated[PasswordManager, Depends(get_password_manager)],
    token_revocation_store: Annotated[TokenRevocationStore, Depends(get_token_revocation_store)],
) -> ChangePasswordWithOtpUseCase:
    """Provide ChangePasswordWithOtpUseCase use case."""
    return ChangePasswordWithOtpUseCase(
        auth_datasource=auth_datasource,
        otp_datasource=otp_datasource,
        password_manager=password_manager,
        token_revocation_store=token_revocation_store,
    )


# === Google OAuth Dependency Providers ===


def get_google_oauth_provider(
    env_config: Annotated[EnvConfig, Depends(get_env_config)],
) -> OAuthProvider:
    """Provide Google OAuth provider implementation."""
    return GoogleOAuthProviderImpl(config=env_config)


def get_google_auth_repository(
    user_provider: Annotated[UserProvider, Depends(get_user_provider)],
) -> GoogleAuthDatasource:
    """Provide Google auth datasource backed by the users port."""
    return GoogleAuthRepository(user_provider=user_provider)


def get_initiate_google_login_use_case(
    oauth_provider: Annotated[OAuthProvider, Depends(get_google_oauth_provider)],
) -> InitiateGoogleLoginUseCase:
    """Provide InitiateGoogleLoginUseCase use case."""
    return InitiateGoogleLoginUseCase(oauth_provider=oauth_provider)


def get_handle_google_callback_use_case(
    oauth_provider: Annotated[OAuthProvider, Depends(get_google_oauth_provider)],
    google_auth_datasource: Annotated[GoogleAuthDatasource, Depends(get_google_auth_repository)],
    token_manager: Annotated[TokenManager, Depends(get_token_manager)],
    token_revocation_store: Annotated[TokenRevocationStore, Depends(get_token_revocation_store)],
) -> HandleGoogleCallbackUseCase:
    """Provide HandleGoogleCallbackUseCase use case."""
    return HandleGoogleCallbackUseCase(
        oauth_provider=oauth_provider,
        google_auth_datasource=google_auth_datasource,
        token_manager=token_manager,
        token_revocation_store=token_revocation_store,
    )


def get_link_google_account_use_case(
    google_auth_datasource: Annotated[GoogleAuthDatasource, Depends(get_google_auth_repository)],
    password_manager: Annotated[PasswordManager, Depends(get_password_manager)],
) -> LinkGoogleAccountUseCase:
    """Provide LinkGoogleAccountUseCase use case."""
    return LinkGoogleAccountUseCase(
        google_auth_datasource=google_auth_datasource,
        password_manager=password_manager,
    )
