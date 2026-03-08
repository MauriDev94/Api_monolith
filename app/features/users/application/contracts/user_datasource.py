from abc import ABC, abstractmethod

from app.features.users.domain.entities.user import User


class UserDatasource(ABC):
    """Application port that defines persistence operations for users."""

    @abstractmethod
    def get_all_users(self) -> list[User]:
        """Return all users available in the data source."""
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> User | None:
        """Return a user by id or None when it does not exist."""
        pass

    @abstractmethod
    def is_email_registered(self, email: str, exclude_user_id: str | None = None) -> bool:
        """Return True when email already belongs to another persisted user."""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Persist complete user changes and return the updated domain entity."""
        pass

    @abstractmethod
    def delete(self, user_id: str) -> None:
        """Delete a user by id."""
        pass
