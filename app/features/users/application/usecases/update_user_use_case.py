from app.common.use_case import UseCase
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.domain.entities.user import User


class UpdateUser(UseCase[UpdateUserParams, User]):
    """Update persisted user data."""

    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self, params: UpdateUserParams) -> User:
        """Persist update payload and return updated entity."""
        return self.user_datasource.update_user(params)
