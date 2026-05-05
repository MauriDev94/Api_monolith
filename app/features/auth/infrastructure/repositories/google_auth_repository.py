"""Google Auth repository implementation."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions.exceptions import ConflictError, DatabaseError
from app.features.auth.application.contracts.google_auth_datasource import GoogleAuthDatasource
from app.features.auth.application.dto.create_google_user_params import CreateGoogleUserParams
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email
from app.features.users.infrastructure.mappers.user_mapper import map_user_model_to_entity
from app.features.users.infrastructure.models.user_model import UserModel


class GoogleAuthRepository(GoogleAuthDatasource):
    """SQLAlchemy implementation of Google auth datasource operations."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_by_id(self, user_id: str) -> User | None:
        """Return user by id or None when it does not exist."""
        try:
            user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to retrieve user by id") from exc

        if user_model is None:
            return None
        return map_user_model_to_entity(user_model)

    def get_user_by_google_id(self, google_id: str) -> User | None:
        """Return user by Google ID or None when it does not exist."""
        try:
            user_model = (
                self.session.query(UserModel).filter(UserModel.google_id == google_id).first()
            )
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to retrieve user by google_id") from exc

        if user_model is None:
            return None
        return map_user_model_to_entity(user_model)

    def get_user_by_email(self, email: str) -> User | None:
        """Return user by normalized email or None when it does not exist."""
        normalized_email = Email(email).value

        try:
            user_model = (
                self.session.query(UserModel).filter(UserModel.email == normalized_email).first()
            )
        except SQLAlchemyError as exc:
            raise DatabaseError("failed to retrieve user by email") from exc

        if user_model is None:
            return None
        return map_user_model_to_entity(user_model)

    def create_google_user(self, params: CreateGoogleUserParams) -> User:
        """Create a new user from Google OAuth data (no password)."""
        normalized_email = Email(params.email).value

        user_model = UserModel(
            id=str(uuid4()),
            name=params.name,
            lastname=params.lastname,
            email=normalized_email,
            password_hash=None,  # Google users don't have password
            birthdate=None,  # Google OAuth doesn't provide birthdate
            google_id=params.google_id,
            google_email_verified=params.google_email_verified,
        )

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

    def link_google_id(self, user_id: str, google_id: str) -> None:
        """Link a Google ID to an existing user."""
        try:
            user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
            if user_model is None:
                return
            user_model.google_id = google_id
            self.session.commit()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseError("failed to link google_id") from exc
