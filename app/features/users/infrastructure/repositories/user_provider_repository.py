from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import ConflictError, DatabaseError
from app.features.users.application.contracts.user_provider import UserProvider
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email
from app.features.users.infrastructure.mappers.user_mapper import (
    map_new_user_entity_to_model,
    map_user_model_to_entity,
)
from app.features.users.infrastructure.models.user_model import UserModel


class UserProviderRepository(UserProvider):
    """SQLAlchemy implementation of the users port consumed by other features.

    Es la dueña de `UserModel` para las operaciones que `auth` necesita; centraliza
    aquí el acceso al ORM de usuarios que antes vivía (acoplado) en auth.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: str) -> User | None:
        try:
            user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to retrieve user by id") from exc
        return map_user_model_to_entity(user_model) if user_model else None

    def get_by_email(self, email: str) -> User | None:
        normalized_email = Email(email).value
        try:
            user_model = (
                self.session.query(UserModel).filter(UserModel.email == normalized_email).first()
            )
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to retrieve user by email") from exc
        return map_user_model_to_entity(user_model) if user_model else None

    def get_by_google_id(self, google_id: str) -> User | None:
        try:
            user_model = (
                self.session.query(UserModel).filter(UserModel.google_id == google_id).first()
            )
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to retrieve user by google_id") from exc
        return map_user_model_to_entity(user_model) if user_model else None

    def create_user(self, user: User) -> User:
        user_model = map_new_user_entity_to_model(user, user_id=str(uuid4()))
        try:
            self.session.add(user_model)
            self.session.commit()
            self.session.refresh(user_model)
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("email already registered") from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to register user") from exc
        return map_user_model_to_entity(user_model)

    def create_google_user(self, user: User) -> User:
        user_model = map_new_user_entity_to_model(user, user_id=str(uuid4()))
        try:
            self.session.add(user_model)
            self.session.commit()
            self.session.refresh(user_model)
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("email or google_id already registered") from exc
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to create google user") from exc
        return map_user_model_to_entity(user_model)

    def update_password(self, user_id: str, password_hash: str) -> None:
        try:
            user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
            if user_model is None:
                return None
            user_model.password_hash = password_hash
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to update user password") from exc
        return None

    def link_google_id(self, user_id: str, google_id: str) -> None:
        try:
            user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
            if user_model is None:
                return None
            user_model.google_id = google_id
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to link google_id") from exc
        return None
