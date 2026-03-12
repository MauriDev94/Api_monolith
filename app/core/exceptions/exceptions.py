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


class InternalServerError(AppError):
    """Mapped to HTTP 500."""


class DatabaseError(AppError):
    """Mapped to HTTP 500 for persistence failures."""


class DatabaseException(DatabaseError):
    """Backwards-compatible alias for database errors."""


class InternalServerErrorException(InternalServerError):
    """Backwards-compatible alias for internal server errors."""


class InvalidCredentialsException(UnauthorizedError):
    """Backwards-compatible alias for invalid credentials."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Invalid email or password")


class ResourceConflictException(ConflictError):
    """Backwards-compatible alias for resource conflicts."""


class ResourceNotFoundException(NotFoundError):
    """Backwards-compatible alias for missing resources."""
