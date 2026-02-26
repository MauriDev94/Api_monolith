from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.auth.application.dto.token_pair_result import TokenPairResult
from app.features.auth.presentation.schemas.auth_requests import RegisterRequest
from app.features.auth.presentation.schemas.auth_responses import (
    AuthUserResponse,
    LoginResponse,
    TokenPairResponse,
)
from app.features.users.domain.entities.user import User


def map_register_request_to_params(request: RegisterRequest) -> RegisterUserParams:
    return RegisterUserParams(
        name=request.name,
        lastname=request.lastname,
        email=str(request.email),
        password=request.password,
        birthdate=request.birthdate,
    )


def map_token_pair_result_to_response(result: TokenPairResult) -> TokenPairResponse:
    return TokenPairResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
    )


def map_token_pair_result_to_login_response(result: TokenPairResult) -> LoginResponse:
    return LoginResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        refresh_token=result.refresh_token,
    )


def map_user_entity_to_auth_user_response(user: User) -> AuthUserResponse:
    return AuthUserResponse(
        id=user.id or "",
        name=user.name,
        lastname=user.lastname,
        email=user.email.value,
        birthdate=user.birthdate,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
