from app.common.use_case import UseCase
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.delete_user_params import DeleteUserParams


class DeleteUser(UseCase[DeleteUserParams, None]):
    """Delete a user by identifier."""

    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self, params: DeleteUserParams) -> None:
        """Delegate deletion to datasource."""
        self.user_datasource.delete(params.user_id)
        return None
