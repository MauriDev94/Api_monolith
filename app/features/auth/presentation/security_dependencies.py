from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.exceptions.exceptions import InternalServerError
from app.features.auth.application.contracts.rate_limiter import RateLimiter
from app.features.auth.application.usecases.get_current_user_use_case import GetCurrentUser
from app.features.auth.di.dependencies import get_current_user_use_case, get_rate_limiter
from app.features.users.domain.entities.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/v1/login")


def get_authenticated_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    use_case: Annotated[GetCurrentUser, Depends(get_current_user_use_case)],
) -> User:
    """Resolve current user from bearer token."""
    return use_case.execute(token)


def enforce_request_otp_rate_limit(
    current_user: Annotated[User, Depends(get_authenticated_user)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Throttle OTP creation attempts by authenticated user."""
    if current_user.id is None:
        raise InternalServerError("user id is missing")
    rate_limiter.check_or_raise(
        key=f"otp:request:{current_user.id}",
        limit=3,
        window_seconds=60,
    )


def enforce_verify_otp_rate_limit(
    current_user: Annotated[User, Depends(get_authenticated_user)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Throttle OTP verification attempts by authenticated user."""
    if current_user.id is None:
        raise InternalServerError("user id is missing")
    rate_limiter.check_or_raise(
        key=f"otp:verify:{current_user.id}",
        limit=5,
        window_seconds=600,
    )
