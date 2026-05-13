"""Link Google account to an existing logged-in user."""

from __future__ import annotations

from dataclasses import dataclass

from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.features.auth.application.contracts.google_auth_datasource import GoogleAuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager


@dataclass(frozen=True, slots=True)
class LinkGoogleAccountParams:
    """Params for linking Google account to logged-in user."""

    user_id: str
    google_id: str
    password: str


@dataclass(frozen=True, slots=True)
class LinkGoogleAccountResult:
    """Result after linking Google account."""

    success: bool
    message: str


class LinkGoogleAccountUseCase(UseCase[LinkGoogleAccountParams, LinkGoogleAccountResult]):
    """Link a Google account to an existing user who is already logged in."""

    def __init__(
        self,
        google_auth_datasource: GoogleAuthDatasource,
        password_manager: PasswordManager,
    ) -> None:
        self._google_auth_datasource = google_auth_datasource
        self._password_manager = password_manager

    def execute(self, params: LinkGoogleAccountParams) -> LinkGoogleAccountResult:
        # Get the user by ID
        user = self._google_auth_datasource.get_user_by_id(params.user_id)
        if user is None:
            raise NotFoundError("User not found")

        if user.google_id is not None:
            raise ConflictError("Google account already linked to this user")

        # Verify password
        if user.password_hash is None:
            raise UnauthorizedError("Cannot link Google account: user has no password")

        is_valid = self._password_manager.verify_password(params.password, user.password_hash)
        if not is_valid:
            raise UnauthorizedError("Invalid password")

        # Link Google ID
        self._google_auth_datasource.link_google_id(params.user_id, params.google_id)

        return LinkGoogleAccountResult(success=True, message="Google account linked successfully")
