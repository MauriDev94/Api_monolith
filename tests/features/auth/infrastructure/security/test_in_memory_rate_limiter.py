import pytest

from app.core.exceptions.exceptions import TooManyRequestsError
from app.features.auth.infrastructure.security.in_memory_rate_limiter import InMemoryRateLimiter


def test_should_allow_hits_within_window_limit() -> None:
    limiter = InMemoryRateLimiter()

    limiter.check_or_raise(key="otp:request:user-1", limit=3, window_seconds=60)
    limiter.check_or_raise(key="otp:request:user-1", limit=3, window_seconds=60)
    limiter.check_or_raise(key="otp:request:user-1", limit=3, window_seconds=60)


def test_should_raise_when_hits_exceed_window_limit() -> None:
    limiter = InMemoryRateLimiter()

    limiter.check_or_raise(key="otp:request:user-1", limit=1, window_seconds=60)

    with pytest.raises(TooManyRequestsError):
        limiter.check_or_raise(key="otp:request:user-1", limit=1, window_seconds=60)
