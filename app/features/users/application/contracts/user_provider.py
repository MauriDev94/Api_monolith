from abc import ABC, abstractmethod

from app.features.users.domain.entities.user import User


class UserProvider(ABC):
    """Puerto público de `users` para que otras features (p.ej. `auth`) operen sobre
    usuarios SIN tocar la infraestructura de users (UserModel/mapper).

    Los datos de entrada son primitivos o la entidad `User` —que es de esta misma
    feature— a propósito: así el contrato nunca se acopla a DTOs de otras features y
    la dependencia queda en una sola dirección (auth → users).

    Las operaciones de creación reciben una entidad ya construida por el dominio
    (`User.create_new` / `User.create_from_google`), de modo que los invariantes se
    validan ANTES de escribir en la base y no al releer la fila.
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
    def create_user(self, user: User) -> User:
        """Persist a password account already built by `User.create_new`."""
        pass

    @abstractmethod
    def create_google_user(self, user: User) -> User:
        """Persist a social account already built by `User.create_from_google`."""
        pass

    @abstractmethod
    def update_password(self, user_id: str, password_hash: str) -> None:
        pass

    @abstractmethod
    def link_google_id(self, user_id: str, google_id: str) -> None:
        pass
