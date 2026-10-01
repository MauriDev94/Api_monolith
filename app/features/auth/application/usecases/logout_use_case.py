from app.common.use_case import UseCase
from app.core.exceptions.exceptions import UnauthorizedError
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.dto.logout_params import LogoutParams


class LogoutUseCase(UseCase[LogoutParams, None]):
    """Revoke every active refresh token for the user, ending all browser sessions.

    Idempotent and non-leaking: missing, empty, tampered, or sub-less tokens
    resolve to a no-op. The endpoint can always invoke this use case and trust
    it to do the right thing.
    """

    def __init__(
        self,
        token_manager: TokenManager,
        token_revocation_store: TokenRevocationStore,
    ) -> None:
        self.token_manager = token_manager
        self.token_revocation_store = token_revocation_store

    def execute(self, params: LogoutParams) -> None:
        if not params.refresh_token:
            return None
        try:
            payload = self.token_manager.decode_refresh_token(params.refresh_token)
        except UnauthorizedError:
            # Tampered or expired token — treat as logout-of-nothing.
            return None
        subject = str(payload.get("sub", ""))
        if subject:
            self.token_revocation_store.revoke_all_for_user(subject)
        return None
