import os
import secrets
from typing import Annotated

from fastapi import Cookie, Depends, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.exceptions.exceptions import InternalServerError, UnauthorizedError
from app.core.router.router import get_versioned_router
from app.features.auth.application.dto.login_user_params import LoginUserParams
from app.features.auth.application.dto.refresh_token_params import RefreshTokenParams
from app.features.auth.application.usecases.change_password_with_otp_use_case import (
    ChangePasswordWithOtpUseCase,
)
from app.features.auth.application.usecases.handle_google_callback import (
    HandleGoogleCallbackParams,
    HandleGoogleCallbackUseCase,
)
from app.features.auth.application.usecases.initiate_google_login import (
    InitiateGoogleLoginParams,
    InitiateGoogleLoginUseCase,
)
from app.features.auth.application.usecases.link_google_account import (
    LinkGoogleAccountParams,
    LinkGoogleAccountUseCase,
)
from app.features.auth.application.usecases.login_user_use_case import LoginUser
from app.features.auth.application.usecases.refresh_access_token_use_case import RefreshAccessToken
from app.features.auth.application.usecases.register_user_use_case import RegisterUser
from app.features.auth.application.usecases.request_otp_use_case import RequestOtpUseCase
from app.features.auth.application.usecases.verify_otp_use_case import VerifyOtpUseCase
from app.features.auth.di.dependencies import (
    get_change_password_with_otp_use_case,
    get_handle_google_callback_use_case,
    get_initiate_google_login_use_case,
    get_link_google_account_use_case,
    get_login_user_use_case,
    get_refresh_access_token_use_case,
    get_register_user_use_case,
    get_request_otp_use_case,
    get_verify_otp_use_case,
)
from app.features.auth.presentation.mappers.auth_mapper import (
    map_change_password_request_to_params,
    map_register_request_to_params,
    map_request_otp_to_params,
    map_token_pair_result_to_login_response,
    map_token_pair_result_to_response,
    map_user_entity_to_auth_user_response,
    map_verify_otp_to_params,
)
from app.features.auth.presentation.schemas.auth_requests import (
    ChangePasswordRequest,
    RefreshTokenRequest,
    RegisterRequest,
    VerifyOtpRequest,
)
from app.features.auth.presentation.schemas.auth_responses import (
    CurrentUserResponse,
    LoginResponse,
    OtpResponse,
    RefreshTokenResponse,
    RegisterResponse,
)
from app.features.auth.presentation.schemas.google_auth_requests import (
    GoogleInitResponse,
    GoogleLinkAccountRequest,
    GoogleLinkAccountResponse,
)
from app.features.auth.presentation.security_dependencies import (
    enforce_login_rate_limit,
    enforce_refresh_rate_limit,
    enforce_register_rate_limit,
    enforce_request_otp_rate_limit,
    enforce_verify_otp_rate_limit,
    get_authenticated_user,
)
from app.features.users.domain.entities.user import User

v1_router = get_versioned_router("v1")


@v1_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    request: RegisterRequest,
    _rate_limit: Annotated[None, Depends(enforce_register_rate_limit)],
    register_user_use_case: Annotated[RegisterUser, Depends(get_register_user_use_case)],
) -> RegisterResponse:
    """Create a user account using validated request payload."""
    user = register_user_use_case.execute(map_register_request_to_params(request))
    return RegisterResponse(user=map_user_entity_to_auth_user_response(user))


@v1_router.post("/login", response_model=LoginResponse)
def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    _rate_limit: Annotated[None, Depends(enforce_login_rate_limit)],
    login_user_use_case: Annotated[LoginUser, Depends(get_login_user_use_case)],
) -> LoginResponse:
    """Authenticate credentials and return access/refresh tokens."""
    result = login_user_use_case.execute(
        LoginUserParams(email=form_data.username, password=form_data.password)
    )
    return map_token_pair_result_to_login_response(result)


@v1_router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_access_token(
    request: RefreshTokenRequest,
    _rate_limit: Annotated[None, Depends(enforce_refresh_rate_limit)],
    refresh_access_token_use_case: Annotated[
        RefreshAccessToken,
        Depends(get_refresh_access_token_use_case),
    ],
) -> RefreshTokenResponse:
    """Issue a new access token from a valid refresh token."""
    result = refresh_access_token_use_case.execute(
        RefreshTokenParams(refresh_token=request.refresh_token)
    )
    return RefreshTokenResponse(tokens=map_token_pair_result_to_response(result))


@v1_router.get("/me", response_model=CurrentUserResponse)
def get_current_user(
    current_user: Annotated[User, Depends(get_authenticated_user)],
) -> CurrentUserResponse:
    """Return authenticated user profile from bearer token."""
    return CurrentUserResponse(user=map_user_entity_to_auth_user_response(current_user))


@v1_router.post("/request-otp", response_model=OtpResponse)
def request_otp(
    _: Annotated[None, Depends(enforce_request_otp_rate_limit)],
    current_user: Annotated[User, Depends(get_authenticated_user)],
    request_otp_use_case: Annotated[RequestOtpUseCase, Depends(get_request_otp_use_case)],
) -> OtpResponse:
    """Generate and deliver a one-time password."""
    if current_user.id is None:
        raise InternalServerError("user id is missing")
    params = map_request_otp_to_params(current_user.id)
    request_otp_use_case.execute(params)
    return OtpResponse(message="OTP sent")


@v1_router.post(
    "/verify-otp",
    response_model=OtpResponse,
    deprecated=True,
    summary="Deprecated: verify OTP (use /change-password)",
)
def verify_otp(
    request: VerifyOtpRequest,
    _: Annotated[None, Depends(enforce_verify_otp_rate_limit)],
    current_user: Annotated[User, Depends(get_authenticated_user)],
    verify_otp_use_case: Annotated[VerifyOtpUseCase, Depends(get_verify_otp_use_case)],
) -> OtpResponse:
    """Deprecated endpoint. Prefer /auth/v1/change-password for password-change flow."""
    if current_user.id is None:
        raise InternalServerError("user id is missing")
    params = map_verify_otp_to_params(request, current_user.id)
    verify_otp_use_case.execute(params)
    return OtpResponse(message="OTP verified")


@v1_router.post("/change-password", response_model=OtpResponse)
def change_password(
    request: ChangePasswordRequest,
    _: Annotated[None, Depends(enforce_verify_otp_rate_limit)],
    current_user: Annotated[User, Depends(get_authenticated_user)],
    change_password_use_case: Annotated[
        ChangePasswordWithOtpUseCase,
        Depends(get_change_password_with_otp_use_case),
    ],
) -> OtpResponse:
    """Change password after validating OTP and revoke active sessions."""
    if current_user.id is None:
        raise InternalServerError("user id is missing")
    params = map_change_password_request_to_params(request, current_user.id)
    change_password_use_case.execute(params)
    return OtpResponse(message="Password changed. Please login again")


# === Google OAuth Endpoints ===

_OAUTH_STATE_COOKIE = "oauth_state"
# Secure solo en producción (HTTPS); en dev/test sobre HTTP la cookie debe poder viajar.
_OAUTH_COOKIE_SECURE = os.getenv("APP_ENV", "dev") == "production"


@v1_router.get("/google", name="google_oauth_init")
def initiate_google_login(
    response: Response,
    initiate_google_login_use_case: Annotated[
        InitiateGoogleLoginUseCase,
        Depends(get_initiate_google_login_use_case),
    ],
) -> GoogleInitResponse:
    """Return Google OAuth authorization URL and bind the CSRF state to the browser."""
    result = initiate_google_login_use_case.execute(InitiateGoogleLoginParams())
    # El state queda atado al navegador vía cookie httpOnly; en el callback se compara
    # contra el `state` que devuelve Google. Sin esto, el callback es vulnerable a CSRF.
    response.set_cookie(
        key=_OAUTH_STATE_COOKIE,
        value=result.state,
        max_age=600,
        httponly=True,
        secure=_OAUTH_COOKIE_SECURE,
        samesite="lax",
    )
    return GoogleInitResponse(authorization_url=result.authorization_url)


@v1_router.get("/google/callback", name="google_oauth_callback")
def handle_google_callback(
    response: Response,
    handle_google_callback_use_case: Annotated[
        HandleGoogleCallbackUseCase,
        Depends(get_handle_google_callback_use_case),
    ],
    code: str = Query(...),
    state: str | None = Query(default=None),
    oauth_state: str | None = Cookie(default=None),
) -> LoginResponse:
    """Handle Google OAuth callback, validate CSRF state, create/link user, return tokens."""
    if not state or not oauth_state or not secrets.compare_digest(state, oauth_state):
        raise UnauthorizedError("Invalid OAuth state")

    result = handle_google_callback_use_case.execute(
        HandleGoogleCallbackParams(code=code, state=state)
    )
    response.delete_cookie(_OAUTH_STATE_COOKIE)
    return map_token_pair_result_to_login_response(result)


@v1_router.post("/link-google", name="link_google_account")
def link_google_account(
    link_google_account_use_case: Annotated[
        LinkGoogleAccountUseCase,
        Depends(get_link_google_account_use_case),
    ],
    current_user: Annotated[User, Depends(get_authenticated_user)],
    request: GoogleLinkAccountRequest,
) -> GoogleLinkAccountResponse:
    """Link a Google account to the currently authenticated user."""
    if current_user.id is None:
        raise InternalServerError("user id is missing")

    params = LinkGoogleAccountParams(
        user_id=current_user.id,
        google_id=request.google_id,
        password=request.password,
    )
    result = link_google_account_use_case.execute(params)
    return GoogleLinkAccountResponse(success=result.success, message=result.message)
