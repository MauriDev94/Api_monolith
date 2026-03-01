class DatabaseException(Exception):
    """Raised when persistence operations fail unexpectedly."""


class InternalServerErrorException(Exception):
    """Raised for unexpected application failures."""


class InvalidCredentialsException(Exception):
    """Raised when authentication credentials are invalid."""


class ResourceConflictException(Exception):
    """Raised when trying to create a resource that already exists."""
