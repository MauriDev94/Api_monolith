from app.common.use_case import UseCase
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.domain.entities.user import User


class UpdateUser(UseCase[UpdateUserParams, User]):
    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self, params: UpdateUserParams) -> User:
        return self.user_datasource.update_user(params)
