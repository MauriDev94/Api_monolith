from sqlalchemy.orm import Session

from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.domain.entities.user import User
from app.features.users.infrastructure.mappers.user_mapper import (
    map_update_user_params_to_model,
    map_user_model_to_entity,
)
from app.features.users.infrastructure.models.user_model import UserModel


class UserRepository(UserDatasource):
    """SQLAlchemy implementation for user persistence operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_all_users(self) -> list[User]:
        """Return all persisted users."""
        users_model = self.session.query(UserModel).all()
        return [map_user_model_to_entity(user_model) for user_model in users_model]

    def get_user_by_id(self, user_id: str) -> User | None:
        """Return a user by id when found."""
        user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        if user_model is None:
            return None
        return map_user_model_to_entity(user_model)

    def update_user(self, params: UpdateUserParams) -> User:
        """Update and return an existing user."""
        user_model = self.session.query(UserModel).filter(UserModel.id == params.id).first()
        if user_model is None:
            raise ValueError("user not found")

        map_update_user_params_to_model(user_model=user_model, params=params)
        self.session.commit()
        self.session.refresh(user_model)
        return map_user_model_to_entity(user_model)

    def delete_user(self, user_id: str) -> None:
        """Delete user when exists and keep operation idempotent."""
        user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        if user_model is None:
            return None

        self.session.delete(user_model)
        self.session.commit()
        return None
