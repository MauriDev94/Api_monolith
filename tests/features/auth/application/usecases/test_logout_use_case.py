from unittest.mock import Mock

from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.dto.logout_params import LogoutParams
from app.features.auth.application.usecases.logout_use_case import LogoutUseCase


# Tipo de test: Unit
def test_should_call_revoke_all_for_user_with_user_id_when_executing_logout() -> None:
    """LogoutUseCase must delegate the bulk revoke to TokenRevocationStore exactly once."""
    token_revocation_store = Mock(spec=TokenRevocationStore)

    use_case = LogoutUseCase(token_revocation_store=token_revocation_store)
    use_case.execute(LogoutParams(user_id="user-1"))

    token_revocation_store.revoke_all_for_user.assert_called_once_with("user-1")


# Tipo de test: Unit
def test_should_not_raise_when_revocation_is_a_noop() -> None:
    """A no-op revoke (no active tokens) must not bubble up as an error."""
    token_revocation_store = Mock(spec=TokenRevocationStore)
    token_revocation_store.revoke_all_for_user.return_value = None

    use_case = LogoutUseCase(token_revocation_store=token_revocation_store)

    # The use case itself must not raise; whatever the store does is the store's contract.
    use_case.execute(LogoutParams(user_id="user-1"))

    token_revocation_store.revoke_all_for_user.assert_called_once_with("user-1")
