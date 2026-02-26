from app.common.use_case import UseCase
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.delete_user_params import DeleteUserParams


class DeleteUser(UseCase[DeleteUserParams, None]):
    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self, params: DeleteUserParams) -> None:
        self.user_datasource.delete_user(params.user_id)
        return None
