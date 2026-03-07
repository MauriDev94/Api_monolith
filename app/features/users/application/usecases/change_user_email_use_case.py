from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ResourceConflictException, ResourceNotFoundException
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.change_user_email_params import ChangeUserEmailParams
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


class ChangeUserEmail(UseCase[ChangeUserEmailParams, User]):
    """Change only the user email."""

    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self, params: ChangeUserEmailParams) -> User:
        """Load user, validate email availability, mutate email, and persist."""
        user = self.user_datasource.get_user_by_id(params.id)
        if user is None:
            raise ResourceNotFoundException("user not found")

        normalized_email = Email(params.email).value
        if user.email.value == normalized_email:
            return user

        if self.user_datasource.is_email_registered(normalized_email, exclude_user_id=user.id):
            raise ResourceConflictException("email already registered")

        user.change_email(normalized_email)
        return self.user_datasource.update_user_email(user)
