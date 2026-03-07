from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import DatabaseException, ResourceConflictException, ResourceNotFoundException
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.domain.entities.user import User
from app.features.users.infrastructure.mappers.user_mapper import (
    map_user_entity_to_model,
    map_user_model_to_entity,
)
from app.features.users.infrastructure.models.user_model import UserModel


class UserRepository(UserDatasource):
    """SQLAlchemy implementation for user persistence operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_all_users(self) -> list[User]:
        """Return all persisted users."""
        try:
            users_model = self.session.query(UserModel).all()
        except SQLAlchemyError as exc:
            raise DatabaseException("failed to retrieve users") from exc

        return [map_user_model_to_entity(user_model) for user_model in users_model]

    def get_user_by_id(self, user_id: str) -> User | None:
        """Return a user by id when found."""
        try:
            user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        except SQLAlchemyError as exc:
            raise DatabaseException("failed to retrieve user by id") from exc

        if user_model is None:
            return None
        return map_user_model_to_entity(user_model)

    def is_email_registered(self, email: str, exclude_user_id: str | None = None) -> bool:
        """Check if email is already assigned to another user."""
        try:
            query = self.session.query(UserModel).filter(UserModel.email == email)
            if exclude_user_id is not None:
                query = query.filter(UserModel.id != exclude_user_id)
            return query.first() is not None
        except SQLAlchemyError as exc:
            raise DatabaseException("failed to check email availability") from exc

    def update_user_profile(self, user: User) -> User:
        """Persist profile-field changes."""
        return self._update_user_entity(user=user, operation="update user profile")

    def update_user_email(self, user: User) -> User:
        """Persist email changes."""
        return self._update_user_entity(user=user, operation="update user email")

    def update_user(self, user: User) -> User:
        """Persist complete mutable user state."""
        return self._update_user_entity(user=user, operation="update user")

    def delete_user(self, user_id: str) -> None:
        """Delete user when exists and keep operation idempotent."""
        try:
            user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        except SQLAlchemyError as exc:
            raise DatabaseException("failed to retrieve user for deletion") from exc

        if user_model is None:
            return None

        try:
            self.session.delete(user_model)
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseException("failed to delete user") from exc

        return None

    def _update_user_entity(self, user: User, operation: str) -> User:
        """Apply mutable entity state to ORM model and persist atomically."""
        if user.id is None:
            raise ResourceNotFoundException("user not found")

        try:
            user_model = self.session.query(UserModel).filter(UserModel.id == user.id).first()
        except SQLAlchemyError as exc:
            raise DatabaseException(f"failed to retrieve user for {operation}") from exc

        if user_model is None:
            raise ResourceNotFoundException("user not found")

        map_user_entity_to_model(user_model=user_model, user=user)

        try:
            self.session.commit()
            self.session.refresh(user_model)
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictException("email already registered") from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseException(f"failed to {operation}") from exc

        return map_user_model_to_entity(user_model)
