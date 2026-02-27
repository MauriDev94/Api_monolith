import traceback

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.exceptions.exceptions import (
    DatabaseException,
    InternalServerErrorException,
    InvalidCredentialsException,
)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Normalize validation errors into a predictable API response."""
    logger.warning(f"Validation error: {exc.errors()}")
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"message": "Validation error", "errors": errors},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """Map HTTP exceptions while hiding details for 5xx responses."""
    if exc.status_code >= 500:
        logger.error(
            f"HTTP 500 Error: {exc.detail}\n",
            f"Path: {request.url.path}\n",
            f"Method: {request.method}",
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
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}\n",
        f"Path: {request.url.path}\n",
        f"Method: {request.method}\n",
        f"Stacktrace:\n{traceback.format_exc()}",
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "message": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


async def database_exception_handler(request: Request, exc: DatabaseException):
    """Handle persistence failures using a dedicated response envelope."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Database error occurred", "detail": str(exc)},
    )


async def internal_server_error_exception_handler(
    request: Request,
    exc: InternalServerErrorException,
):
    """Handle known internal failures raised by the application layer."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error", "detail": str(exc)},
    )


async def invalid_credentials_exception_handler(request: Request, exc: InvalidCredentialsException):
    """Return a stable unauthorized response for invalid credentials."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"message": "Invalid email or password"},
    )


def register_exception_handlers(app: FastAPI):
    """Register all global exception handlers in priority order."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(DatabaseException, database_exception_handler)
    app.add_exception_handler(InternalServerErrorException, internal_server_error_exception_handler)
    app.add_exception_handler(InvalidCredentialsException, invalid_credentials_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
