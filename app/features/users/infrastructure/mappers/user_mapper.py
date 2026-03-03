from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email
from app.features.users.infrastructure.models.user_model import UserModel


def map_user_model_to_entity(user_model: UserModel) -> User:
    """Map ORM user model to domain entity."""
    return User(
        id=user_model.id,
        name=user_model.name,
        lastname=user_model.lastname,
        email=Email(user_model.email),
        password_hash=user_model.password_hash,
        birthdate=user_model.birthdate,
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
    )


def map_update_user_params_to_model(user_model: UserModel, params: UpdateUserParams) -> UserModel:
    """Apply update DTO values into an existing ORM model instance."""
    user_model.name = params.name
    user_model.lastname = params.lastname
    user_model.email = params.email
    user_model.birthdate = params.birthdate
    return user_model
