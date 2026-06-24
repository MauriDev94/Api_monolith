"""Google Auth repository: adapter over the users port."""

from __future__ import annotations

from app.features.auth.application.contracts.google_auth_datasource import GoogleAuthDatasource
from app.features.auth.application.dto.create_google_user_params import CreateGoogleUserParams
from app.features.users.application.contracts.user_provider import UserProvider
from app.features.users.domain.entities.user import User


class GoogleAuthRepository(GoogleAuthDatasource):
    """Adapter that fulfils Google-auth's user needs via the users port.

    No toca UserModel ni el mapper de users: delega en `UserProvider`.
    """

    def __init__(self, user_provider: UserProvider) -> None:
        self._users = user_provider

    def get_user_by_id(self, user_id: str) -> User | None:
        return self._users.get_by_id(user_id)

    def get_user_by_google_id(self, google_id: str) -> User | None:
        return self._users.get_by_google_id(google_id)

    def get_user_by_email(self, email: str) -> User | None:
        return self._users.get_by_email(email)

    def create_google_user(self, params: CreateGoogleUserParams) -> User:
        return self._users.create_google_user(
            google_id=params.google_id,
            email=params.email,
            name=params.name,
            lastname=params.lastname,
            google_email_verified=params.google_email_verified,
        )

    def link_google_id(self, user_id: str, google_id: str) -> None:
        self._users.link_google_id(user_id, google_id)
