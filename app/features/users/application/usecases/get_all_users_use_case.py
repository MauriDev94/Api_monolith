from app.common.use_case_no_params import UseCaseNoParams
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.domain.entities.user import User


class GetAllUsers(UseCaseNoParams[list[User]]):
    """Retrieve all users from datasource."""

    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self) -> list[User]:
        """Run query and return mapped domain entities."""
        return self.user_datasource.get_all_users()
