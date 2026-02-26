from uuid import uuid4

from sqlalchemy.orm import Session

from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.users.domain.entities.user import User
from app.features.users.infrastructure.mappers.user_mapper import map_user_model_to_entity
from app.features.users.infrastructure.models.user_model import UserModel


class AuthRepository(AuthDatasource):
    def __init__(self, session: Session):
        self.session = session

    def get_user_by_id(self, user_id: str) -> User | None:
        user_model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        if user_model is None:
            return None
        return map_user_model_to_entity(user_model)

    def get_user_by_email(self, email: str) -> User | None:
        user_model = self.session.query(UserModel).filter(UserModel.email == email).first()
        if user_model is None:
            return None
        return map_user_model_to_entity(user_model)

    def register_user(self, params: RegisterUserParams, password_hash: str) -> User:
        user_model = UserModel(
            id=str(uuid4()),
            name=params.name,
            lastname=params.lastname,
            email=params.email,
            password_hash=password_hash,
            birthdate=params.birthdate,
        )
        self.session.add(user_model)
        self.session.commit()
        self.session.refresh(user_model)
        return map_user_model_to_entity(user_model)
