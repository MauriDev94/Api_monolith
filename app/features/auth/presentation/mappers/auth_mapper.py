from app.core.exceptions.exceptions import InternalServerError
from app.features.auth.application.constants import OTP_PURPOSE_PASSWORD_CHANGE
from app.features.auth.application.dto.change_password_with_otp_params import (
    ChangePasswordWithOtpParams,
)
from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.auth.application.dto.request_otp_params import RequestOtpParams
from app.features.auth.application.dto.token_pair_result import TokenPairResult
from app.features.auth.application.dto.verify_otp_params import VerifyOtpParams
from app.features.auth.presentation.schemas.auth_requests import (
    ChangePasswordRequest,
    RegisterRequest,
    VerifyOtpRequest,
)
from app.features.auth.presentation.schemas.auth_responses import (
    AuthUserResponse,
    LoginResponse,
    TokenPairResponse,
)
from app.features.users.domain.entities.user import User


def map_register_request_to_params(request: RegisterRequest) -> RegisterUserParams:
    """Map register request payload to use-case parameters."""
    return RegisterUserParams(
        name=request.name,
        lastname=request.lastname,
        email=str(request.email),
        password=request.password,
        birthdate=request.birthdate,
    )


def map_token_pair_result_to_response(result: TokenPairResult) -> TokenPairResponse:
    """Map token result DTO to generic token response schema."""
    return TokenPairResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
    )


def map_token_pair_result_to_login_response(result: TokenPairResult) -> LoginResponse:
    """Map token result DTO to login response schema."""
    return LoginResponse(
        access_token=result.access_token,
        token_type=result.token_type,
        refresh_token=result.refresh_token,
    )


def map_user_entity_to_auth_user_response(user: User) -> AuthUserResponse:
    """Map user entity to public auth user response."""
    if user.id is None:
        raise InternalServerError("user id is missing")
    return AuthUserResponse(
        id=user.id,
        name=user.name,
        lastname=user.lastname,
        email=user.email.value,
        birthdate=user.birthdate,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def map_request_otp_to_params(user_id: str) -> RequestOtpParams:
    """Map OTP request payload to use-case params."""
    return RequestOtpParams(user_id=user_id, purpose=OTP_PURPOSE_PASSWORD_CHANGE)


def map_verify_otp_to_params(request: VerifyOtpRequest, user_id: str) -> VerifyOtpParams:
    """Map OTP verify payload to use-case params."""
    return VerifyOtpParams(
        user_id=user_id,
        code=request.code,
        purpose=OTP_PURPOSE_PASSWORD_CHANGE,
    )


def map_change_password_request_to_params(
    request: ChangePasswordRequest,
    user_id: str,
) -> ChangePasswordWithOtpParams:
    """Map password-change payload to use-case params."""
    return ChangePasswordWithOtpParams(
        user_id=user_id,
        code=request.code,
        new_password=request.new_password,
    )
