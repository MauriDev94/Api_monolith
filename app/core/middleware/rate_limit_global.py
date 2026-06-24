from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.http_utils import get_client_ip
from app.features.auth.infrastructure.security.in_memory_rate_limiter import InMemoryRateLimiter

# Global rate limiter configuration
# Adjust these values based on production needs
DEFAULT_RATE_LIMIT = 100  # requests per window
DEFAULT_WINDOW_SECONDS = 60  # window in seconds


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware for all public endpoints.

    Applies rate limiting to prevent abuse of public APIs.
    Uses in-memory storage - for production use Redis or similar.
    """

    def __init__(
        self,
        app,
        rate_limit: int = DEFAULT_RATE_LIMIT,
        window_seconds: int = DEFAULT_WINDOW_SECONDS,
    ) -> None:
        super().__init__(app)
        self.rate_limiter = InMemoryRateLimiter()
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for health checks and docs
        path = request.url.path
        if path in ["/", "/docs", "/openapi.json", "/health"]:
            return await call_next(request)

        # Client IP from the trusted edge (rightmost X-Forwarded-For), not spoofable.
        key = f"global:{get_client_ip(request)}"

        try:
            self.rate_limiter.check_or_raise(key, self.rate_limit, self.window_seconds)
        except Exception:
            return JSONResponse(
                status_code=429, content={"detail": "Too many requests, try again later"}
            )

        return await call_next(request)
