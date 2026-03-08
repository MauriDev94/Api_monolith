from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ResourceConflictException, ResourceNotFoundException
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


class UpdateUser(UseCase[UpdateUserParams, User]):
    """Update user profile and email in a single application flow."""

    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self, params: UpdateUserParams) -> User:
        """Load user, apply domain mutations, validate email uniqueness, and persist once."""
        user = self.user_datasource.get_user_by_id(params.id)
        if user is None:
            raise ResourceNotFoundException("user not found")

        user.change_name(params.name)
        user.change_lastname(params.lastname)
        user.change_birthdate(params.birthdate)

        normalized_email = Email(params.email).value
        if user.email.value != normalized_email:
            if self.user_datasource.is_email_registered(normalized_email, exclude_user_id=user.id):
                raise ResourceConflictException("email already registered")
            user.change_email(normalized_email)

        return self.user_datasource.update(user)
