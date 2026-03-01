from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import DatabaseException, ResourceConflictException
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.users.domain.entities.user import User
from app.features.users.infrastructure.mappers.user_mapper import map_user_model_to_entity
from app.features.users.infrastructure.models.user_model import UserModel


class AuthRepository(AuthDatasource):
    """SQLAlchemy implementation of auth datasource operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_user_by_id(self, user_id: str) -> User | None:
        """Return user by id or None when it does not exist."""
        try:
            user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        except SQLAlchemyError as exc:
            raise DatabaseException("failed to retrieve user by id") from exc

        if user_model is None:
            return None
        return map_user_model_to_entity(user_model)

    def get_user_by_email(self, email: str) -> User | None:
        """Return user by email or None when it does not exist."""
        try:
            user_model = self.session.query(UserModel).filter(UserModel.email == email).first()
        except SQLAlchemyError as exc:
            raise DatabaseException("failed to retrieve user by email") from exc

        if user_model is None:
            return None
        return map_user_model_to_entity(user_model)

    def register_user(self, params: RegisterUserParams, password_hash: str) -> User:
        """Persist new user and map technical errors to app-level exceptions."""
        user_model = UserModel(
            id=str(uuid4()),
            name=params.name,
            lastname=params.lastname,
            email=params.email,
            password_hash=password_hash,
            birthdate=params.birthdate,
        )

        try:
            self.session.add(user_model)
            self.session.commit()
            self.session.refresh(user_model)
        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictException("email already registered") from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseException("failed to register user") from exc

        return map_user_model_to_entity(user_model)
