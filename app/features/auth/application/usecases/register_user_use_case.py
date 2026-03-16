from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ConflictError
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.dto.register_user_params import RegisterUserParams
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


class RegisterUser(UseCase[RegisterUserParams, User]):
    """Register user flow with uniqueness validation and password hashing."""

    def __init__(self, auth_datasource: AuthDatasource, password_manager: PasswordManager):
        self.auth_datasource = auth_datasource
        self.password_manager = password_manager

    def execute(self, params: RegisterUserParams) -> User:
        normalized_email = Email(params.email).value

        existing_user = self.auth_datasource.get_user_by_email(normalized_email)
        if existing_user is not None:
            raise ConflictError("email already registered")

        password_hash = self.password_manager.hash_password(params.password)
        normalized_params = RegisterUserParams(
            name=params.name,
            lastname=params.lastname,
            email=normalized_email,
            password=params.password,
            birthdate=params.birthdate,
        )
        return self.auth_datasource.register_user(params=normalized_params, password_hash=password_hash)
