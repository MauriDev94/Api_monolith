from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.users.application.contracts.user_provider import UserProvider
from app.features.users.domain.entities.user import User


class AuthRepository(AuthDatasource):
    """Adapter that fulfils auth's user-persistence needs via the users port.

    No toca UserModel ni el mapper de users: delega en `UserProvider`, que es el
    contrato público de la feature `users`.
    """

    def __init__(self, user_provider: UserProvider):
        self._users = user_provider

    def get_user_by_id(self, user_id: str) -> User | None:
        return self._users.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        return self._users.get_by_email(email)

    def register_user(self, user: User) -> User:
        return self._users.create_user(user)

    def update_password(self, user_id: str, password_hash: str) -> None:
        self._users.update_password(user_id, password_hash)
