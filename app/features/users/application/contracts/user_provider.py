from abc import ABC, abstractmethod
from datetime import date

from app.features.users.domain.entities.user import User


class UserProvider(ABC):
    """Puerto público de `users` para que otras features (p.ej. `auth`) operen sobre
    usuarios SIN tocar la infraestructura de users (UserModel/mapper).

    Recibe parámetros primitivos a propósito: así el contrato no se acopla a DTOs de
    otras features y la dependencia queda en una sola dirección (auth → users).
    """

    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    def get_by_google_id(self, google_id: str) -> User | None:
        pass

    @abstractmethod
    def create_user(
        self,
        name: str,
        lastname: str,
        email: str,
        password_hash: str,
        birthdate: date | None,
    ) -> User:
        pass

    @abstractmethod
    def create_google_user(
        self,
        google_id: str,
        email: str,
        name: str,
        lastname: str,
        google_email_verified: bool,
    ) -> User:
        pass

    @abstractmethod
    def update_password(self, user_id: str, password_hash: str) -> None:
        pass

    @abstractmethod
    def link_google_id(self, user_id: str, google_id: str) -> None:
        pass
