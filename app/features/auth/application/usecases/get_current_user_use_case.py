from app.common.use_case import UseCase
from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.users.domain.entities.user import User


class GetCurrentUser(UseCase[str, User]):
    """Resolve current authenticated user from a bearer token."""

    def __init__(self, auth_datasource: AuthDatasource, token_manager: TokenManager):
        self.auth_datasource = auth_datasource
        self.token_manager = token_manager

    def execute(self, params: str) -> User:
        payload = self.token_manager.decode_access_token(params)
        subject = str(payload.get("sub", ""))
        if not subject:
            raise ValueError("invalid token")

        user = self.auth_datasource.get_user_by_id(subject)
        if user is None:
            raise ValueError("invalid token")
        return user
