import pytest

from app.core.config.env_config import EnvConfig
from app.core.data.source.local.database import Database

_DB_VARS = ("DB_USER", "DB_PASSWORD", "DB_NAME", "DB_PORT", "DB_HOST")


# Tipo de test: Unit
def test_env_config_allows_db_fields_to_be_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """En prod (Render) solo se inyecta DATABASE_URL + jwt; los db_* son opcionales."""
    for var in _DB_VARS:
        monkeypatch.delenv(var, raising=False)

    config = EnvConfig(_env_file=None, jwt_secret_key="secret-key")  # type: ignore[call-arg]

    assert config.jwt_secret_key == "secret-key"
    assert config.db_user is None
    assert config.db_host is None
    assert config.db_port is None


# Tipo de test: Unit
def test_database_raises_clear_error_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sin DATABASE_URL ni db_*, Database falla con un mensaje claro (no una URL inválida)."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    for var in _DB_VARS:
        monkeypatch.delenv(var, raising=False)
    config = EnvConfig(_env_file=None, jwt_secret_key="secret-key")  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="Database not configured"):
        Database(config)
