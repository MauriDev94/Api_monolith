import traceback

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.common.domain_error import DomainError
from app.core.exceptions.exceptions import (
    ConflictError,
    DatabaseError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
    ValidationError,
)


def _request_logger(request: Request):
    """Return logger bound with current request id for consistent correlation."""
    request_id = getattr(request.state, "request_id", "-")
    return logger.bind(request_id=request_id)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Normalize validation errors into a predictable API response."""
    errors = [
        {
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    # No loguear exc.errors() crudo: incluye la clave 'input' con el valor enviado,
    # lo que filtra datos sensibles (p.ej. passwords) en texto plano a los logs (OWASP A09).
    _request_logger(request).warning(f"Validation error: {errors}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Validation error", "errors": errors},
    )


async def domain_error_exception_handler(request: Request, exc: DomainError):
    """Map domain invariant violations to 400.

    Solo DomainError (que el dominio lanza explícitamente) se trata como error del
    cliente. Un ValueError "pelado" (no esperado, normalmente un bug) NO se maneja aquí:
    cae al handler genérico → 500, en vez de disfrazarse de 400.
    """
    _request_logger(request).warning(f"DomainError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": str(exc) or "Validation error"},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Map HTTP exceptions while hiding details for 5xx responses."""
    request_logger = _request_logger(request)
    if exc.status_code >= 500:
        request_logger.error(
            f"HTTP 500 Error: {exc.detail} | Path: {request.url.path} | Method: {request.method}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": "Internal server error",
                "detail": "An unexpected error occurred. Please try again later.",
            },
        )

    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


async def generic_exception_handler(request: Request, exc: Exception):
    """Fallback handler for unexpected exceptions with stack trace logging."""
    _request_logger(request).error(
        f"Unhandled exception: {type(exc).__name__}: {exc!s} | "
        f"Path: {request.url.path} | Method: {request.method}\n"
        f"Stacktrace:\n{traceback.format_exc()}"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle persistence failures using a dedicated response envelope."""
    _request_logger(request).error(f"DatabaseError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Database error occurred",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


async def internal_server_error_exception_handler(
    request: Request,
    exc: InternalServerError,
):
    """Handle known internal failures raised by the application layer."""
    _request_logger(request).error(f"InternalServerError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


async def unauthorized_exception_handler(request: Request, exc: UnauthorizedError):
    """Return a stable unauthorized response for invalid credentials."""
    _request_logger(request).warning(f"UnauthorizedError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": str(exc) or "Unauthorized"},
    )


async def forbidden_exception_handler(request: Request, exc: ForbiddenError):
    """Return a forbidden response for access control violations."""
    _request_logger(request).warning(f"ForbiddenError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"message": str(exc) or "Forbidden"},
    )


async def resource_conflict_exception_handler(request: Request, exc: ConflictError):
    """Return a conflict response when resource uniqueness is violated."""
    _request_logger(request).warning(f"ConflictError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"message": str(exc) or "Resource already exists"},
    )


async def resource_not_found_exception_handler(request: Request, exc: NotFoundError):
    """Return a not-found response for missing resources."""
    _request_logger(request).warning(f"NotFoundError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": str(exc) or "Resource not found"},
    )


async def validation_error_exception_handler(request: Request, exc: ValidationError):
    """Return a validation response for domain/application validation errors."""
    _request_logger(request).warning(f"ValidationError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": str(exc) or "Validation error"},
    )


async def too_many_requests_exception_handler(
    request: Request,
    exc: TooManyRequestsError,
):
    """Return a rate-limit response for excessive request bursts."""
    _request_logger(request).warning(f"TooManyRequestsError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"message": str(exc) or "Too many requests"},
    )


def register_exception_handlers(app: FastAPI):
    """Register all global exception handlers in priority order."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_error_exception_handler)
    app.add_exception_handler(DomainError, domain_error_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(InternalServerError, internal_server_error_exception_handler)
    app.add_exception_handler(UnauthorizedError, unauthorized_exception_handler)
    app.add_exception_handler(ForbiddenError, forbidden_exception_handler)
    app.add_exception_handler(ConflictError, resource_conflict_exception_handler)
    app.add_exception_handler(NotFoundError, resource_not_found_exception_handler)
    app.add_exception_handler(TooManyRequestsError, too_many_requests_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
