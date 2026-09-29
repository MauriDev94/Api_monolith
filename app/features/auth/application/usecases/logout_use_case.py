from app.common.use_case import UseCase
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.dto.logout_params import LogoutParams


class LogoutUseCase(UseCase[LogoutParams, None]):
    """Revoke every active refresh token for the user, ending all browser sessions."""

    def __init__(self, token_revocation_store: TokenRevocationStore) -> None:
        self.token_revocation_store = token_revocation_store

    def execute(self, params: LogoutParams) -> None:
        self.token_revocation_store.revoke_all_for_user(params.user_id)
        return None
