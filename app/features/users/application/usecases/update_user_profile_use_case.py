from app.common.use_case import UseCase
from app.core.exceptions.exceptions import ResourceNotFoundException
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.update_user_profile_params import UpdateUserProfileParams
from app.features.users.domain.entities.user import User


class UpdateUserProfile(UseCase[UpdateUserProfileParams, User]):
    """Update profile fields except email."""

    def __init__(self, user_datasource: UserDatasource):
        self.user_datasource = user_datasource

    def execute(self, params: UpdateUserProfileParams) -> User:
        """Load user, mutate profile fields in domain, and persist."""
        user = self.user_datasource.get_user_by_id(params.id)
        if user is None:
            raise ResourceNotFoundException("user not found")

        user.change_name(params.name)
        user.change_lastname(params.lastname)
        user.change_birthdate(params.birthdate)

        return self.user_datasource.update_user_profile(user)
