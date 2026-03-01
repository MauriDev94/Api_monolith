from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ResourceNotFoundException
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.get_user_by_id_params import GetUserByIdParams
from app.features.users.domain.entities.user import User


class GetUserById(UseCase[GetUserByIdParams, User]):
    """Retrieve a user by identifier."""

    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self, params: GetUserByIdParams) -> User:
        """Return user when it exists, otherwise raise not-found error."""
        user = self.user_datasource.get_user_by_id(params.user_id)
        if user is None:
            raise ResourceNotFoundException("user not found")
        return user
