from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ResourceNotFoundException
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.change_user_email_params import ChangeUserEmailParams
from app.features.users.domain.entities.user import User


class ChangeUserEmail(UseCase[ChangeUserEmailParams, User]):
    """Change only the user email."""

    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self, params: ChangeUserEmailParams) -> User:
        """Load user, mutate email in domain, and persist."""
        user = self.user_datasource.get_user_by_id(params.id)
        if user is None:
            raise ResourceNotFoundException("user not found")

        user.change_email(params.email)

        return self.user_datasource.update_user(user)
