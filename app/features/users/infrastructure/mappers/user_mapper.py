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


def map_user_entity_to_model(user_model: UserModel, user: User) -> UserModel:
    """Apply mutable domain user state into an existing ORM model instance."""
    user_model.name = user.name
    user_model.lastname = user.lastname
    user_model.email = user.email.value
    user_model.birthdate = user.birthdate
    user_model.updated_at = user.updated_at
    return user_model
