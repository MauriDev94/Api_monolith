from unittest.mock import Mock

from app.core.exceptions.exceptions import UnauthorizedError
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.application.dto.logout_params import LogoutParams
from app.features.auth.application.usecases.logout_use_case import LogoutUseCase


def _make_use_case() -> tuple[LogoutUseCase, Mock, Mock]:
    """Build a LogoutUseCase with both dependencies mocked and isolated."""
    token_manager = Mock(spec=TokenManager)
    token_revocation_store = Mock(spec=TokenRevocationStore)
    use_case = LogoutUseCase(
        token_manager=token_manager,
        token_revocation_store=token_revocation_store,
    )
    return use_case, token_manager, token_revocation_store


# Tipo de test: Unit
def test_should_call_revoke_all_for_user_when_token_decodes_successfully() -> None:
    """A valid refresh token must yield the subject and trigger bulk revoke."""
    use_case, token_manager, token_revocation_store = _make_use_case()
    token_manager.decode_refresh_token.return_value = {"sub": "user-1"}

    use_case.execute(LogoutParams(refresh_token="valid-token"))

    token_manager.decode_refresh_token.assert_called_once_with("valid-token")
    token_revocation_store.revoke_all_for_user.assert_called_once_with("user-1")


# Tipo de test: Unit
def test_should_not_call_decode_or_revoke_when_refresh_token_is_none() -> None:
    """Missing token must short-circuit the use case (no DB or token work)."""
    use_case, token_manager, token_revocation_store = _make_use_case()

    use_case.execute(LogoutParams(refresh_token=None))

    token_manager.decode_refresh_token.assert_not_called()
    token_revocation_store.revoke_all_for_user.assert_not_called()


# Tipo de test: Unit
def test_should_not_call_decode_or_revoke_when_refresh_token_is_empty() -> None:
    """Empty token must short-circuit the use case."""
    use_case, token_manager, token_revocation_store = _make_use_case()

    use_case.execute(LogoutParams(refresh_token=""))

    token_manager.decode_refresh_token.assert_not_called()
    token_revocation_store.revoke_all_for_user.assert_not_called()


# Tipo de test: Unit
def test_should_not_call_revoke_when_token_decode_raises() -> None:
    """Tampered/expired token must NOT trigger revocation (idempotent + no leakage)."""
    use_case, token_manager, token_revocation_store = _make_use_case()
    token_manager.decode_refresh_token.side_effect = UnauthorizedError("bad token")

    use_case.execute(LogoutParams(refresh_token="tampered.value"))

    token_manager.decode_refresh_token.assert_called_once_with("tampered.value")
    token_revocation_store.revoke_all_for_user.assert_not_called()


# Tipo de test: Unit
def test_should_not_call_revoke_when_payload_has_no_subject() -> None:
    """A token without a `sub` claim must NOT trigger revocation."""
    use_case, token_manager, token_revocation_store = _make_use_case()
    token_manager.decode_refresh_token.return_value = {}

    use_case.execute(LogoutParams(refresh_token="subless-token"))

    token_manager.decode_refresh_token.assert_called_once_with("subless-token")
    token_revocation_store.revoke_all_for_user.assert_not_called()
