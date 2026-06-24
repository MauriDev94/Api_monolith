from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.core.exceptions.exceptions import InternalServerError
from app.core.http_utils import get_client_ip
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


def enforce_login_rate_limit(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Throttle login: por email (protege la cuenta, NO falsificable) y por IP.

    Limitar por el email atacado es inmune al spoofing de IP — el atacante no puede
    cambiar la cuenta objetivo que está intentando reventar. El límite por IP es
    defensa en profundidad (best-effort) contra credential stuffing distribuido.
    """
    rate_limiter.check_or_raise(
        key=f"login:email:{form_data.username.strip().lower()}", limit=10, window_seconds=300
    )
    rate_limiter.check_or_raise(
        key=f"login:ip:{get_client_ip(request)}", limit=30, window_seconds=60
    )


def enforce_register_rate_limit(
    request: Request,
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Throttle account creation por IP (anti spam de cuentas)."""
    rate_limiter.check_or_raise(
        key=f"register:{get_client_ip(request)}", limit=5, window_seconds=60
    )


def enforce_refresh_rate_limit(
    request: Request,
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Throttle token refresh por IP."""
    rate_limiter.check_or_raise(
        key=f"refresh:{get_client_ip(request)}", limit=30, window_seconds=60
    )
