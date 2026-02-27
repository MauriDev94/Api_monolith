from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.router.router import get_versioned_router
from app.features.auth.application.dto.login_user_params import LoginUserParams
from app.features.auth.application.dto.refresh_token_params import RefreshTokenParams
from app.features.auth.application.usecases.login_user_use_case import LoginUser
from app.features.auth.application.usecases.refresh_access_token_use_case import RefreshAccessToken
from app.features.auth.application.usecases.register_user_use_case import RegisterUser
from app.features.auth.di.dependencies import (
    get_login_user_use_case,
    get_refresh_access_token_use_case,
    get_register_user_use_case,
)
from app.features.auth.presentation.mappers.auth_mapper import (
    map_register_request_to_params,
    map_token_pair_result_to_login_response,
    map_token_pair_result_to_response,
    map_user_entity_to_auth_user_response,
)
from app.features.auth.presentation.schemas.auth_requests import (
    RefreshTokenRequest,
    RegisterRequest,
)
from app.features.auth.presentation.schemas.auth_responses import (
    CurrentUserResponse,
    LoginResponse,
    RefreshTokenResponse,
    RegisterResponse,
)
from app.features.auth.presentation.security_dependencies import get_authenticated_user
from app.features.users.domain.entities.user import User

v1_router = get_versioned_router("v1")


@v1_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    request: RegisterRequest,
    register_user_use_case: Annotated[RegisterUser, Depends(get_register_user_use_case)],
) -> RegisterResponse:
    """Create a user account using validated request payload."""
    try:
        user = register_user_use_case.execute(map_register_request_to_params(request))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return RegisterResponse(user=map_user_entity_to_auth_user_response(user))


@v1_router.post("/login", response_model=LoginResponse)
def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    login_user_use_case: Annotated[LoginUser, Depends(get_login_user_use_case)],
) -> LoginResponse:
    """Authenticate credentials and return access/refresh tokens."""
    try:
        result = login_user_use_case.execute(
            LoginUserParams(email=form_data.username, password=form_data.password)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return map_token_pair_result_to_login_response(result)


@v1_router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_access_token(
    request: RefreshTokenRequest,
    refresh_access_token_use_case: Annotated[
        RefreshAccessToken,
        Depends(get_refresh_access_token_use_case),
    ],
) -> RefreshTokenResponse:
    """Issue a new access token from a valid refresh token."""
    try:
        result = refresh_access_token_use_case.execute(
            RefreshTokenParams(refresh_token=request.refresh_token)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return RefreshTokenResponse(tokens=map_token_pair_result_to_response(result))


@v1_router.get("/me", response_model=CurrentUserResponse)
def get_current_user(
    current_user: Annotated[User, Depends(get_authenticated_user)],
) -> CurrentUserResponse:
    """Return authenticated user profile from bearer token."""
    return CurrentUserResponse(user=map_user_entity_to_auth_user_response(current_user))
