class AppError(Exception):
    """Base class for domain/application errors mapped to HTTP responses."""


class NotFoundError(AppError):
    """Mapped to HTTP 404."""


class ConflictError(AppError):
    """Mapped to HTTP 409."""


class UnauthorizedError(AppError):
    """Mapped to HTTP 401."""


class ForbiddenError(AppError):
    """Mapped to HTTP 403."""


class ValidationError(AppError):
    """Mapped to HTTP 422."""


class TooManyRequestsError(AppError):
    """Mapped to HTTP 429."""


class InternalServerError(AppError):
    """Mapped to HTTP 500."""


class DatabaseError(AppError):
    """Mapped to HTTP 500 for persistence failures."""
