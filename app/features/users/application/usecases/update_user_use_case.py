from app.common.use_case import UseCase
from app.features.users.application.contracts.user_datasource import UserDatasource
from app.features.users.application.dto.change_user_email_params import ChangeUserEmailParams
from app.features.users.application.dto.update_user_params import UpdateUserParams
from app.features.users.application.dto.update_user_profile_params import UpdateUserProfileParams
from app.features.users.application.usecases.change_user_email_use_case import ChangeUserEmail
from app.features.users.application.usecases.update_user_profile_use_case import UpdateUserProfile
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email


class UpdateUser(UseCase[UpdateUserParams, User]):
    """Orchestrate profile update and email change while preserving current API contract."""

    def __init__(
        self,
        user_datasource: UserDatasource,
        update_user_profile_use_case: UpdateUserProfile | None = None,
        change_user_email_use_case: ChangeUserEmail | None = None,
    ):
        self.update_user_profile_use_case = update_user_profile_use_case or UpdateUserProfile(user_datasource)
        self.change_user_email_use_case = change_user_email_use_case or ChangeUserEmail(user_datasource)

    def execute(self, params: UpdateUserParams) -> User:
        """Apply profile changes first, then apply email mutation if it actually changed."""
        user = self.update_user_profile_use_case.execute(
            UpdateUserProfileParams(
                id=params.id,
                name=params.name,
                lastname=params.lastname,
                birthdate=params.birthdate,
            )
        )

        normalized_email = Email(params.email).value
        if user.email.value == normalized_email:
            return user

        return self.change_user_email_use_case.execute(
            ChangeUserEmailParams(
                id=params.id,
                email=params.email,
            )
        )
