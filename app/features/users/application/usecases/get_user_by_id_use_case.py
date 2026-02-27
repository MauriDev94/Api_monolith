from app.common.use_case import UseCase
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.get_user_by_id_params import GetUserByIdParams
from app.features.users.domain.entities.user import User


class GetUserById(UseCase[GetUserByIdParams, User | None]):
    """Retrieve a user by identifier."""

    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self, params: GetUserByIdParams) -> User | None:
        """Return user when it exists, otherwise None."""
        return self.user_datasource.get_user_by_id(params.user_id)
