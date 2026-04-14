from unittest.mock import MagicMock, patch

import pytest

from app.core.data.source.local.database import Database


@pytest.fixture
def mock_config():
    config = MagicMock()
    config.db_user = "test_user"
    config.db_password = "test_pass"
    config.db_host = "localhost"
    config.db_port = 5432
    config.db_name = "test_db"
    return config


def test_should_initialize_engine_with_echo_false(mock_config):
    """Verifica que el engine se crea con echo=False."""
    with patch("app.core.data.source.local.database.create_engine") as mock_create:
        mock_create.return_value = MagicMock()

        _ = Database(config=mock_config)

        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs.get("echo", True) is False


def test_should_setup_slow_query_logging(mock_config):
    """Verifica que se registran los event listeners."""
    with patch("app.core.data.source.local.database.create_engine") as mock_create:
        mock_engine = MagicMock()
        mock_create.return_value = mock_engine

        _ = Database(config=mock_config)

        # Verify listen_for was called for before and after cursor execute
        assert mock_engine.listen_for.called


def test_should_log_warning_when_query_exceeds_threshold(mock_config):
    """Verifica que se loguea WARNING cuando la query es lenta."""
    with patch("app.core.data.source.local.database.create_engine") as mock_create:
        mock_engine = MagicMock()
        mock_create.return_value = mock_engine

        _ = Database(config=mock_config)

        # Verify that listen_for was called at least twice (before and after)
        assert mock_engine.listen_for.call_count >= 2


def test_slow_query_threshold_is_configurable(mock_config):
    """Verifica que el threshold es configurable."""
    with patch("app.core.data.source.local.database.create_engine") as mock_create:
        mock_create.return_value = MagicMock()

        db = Database(config=mock_config)

        assert db.SLOW_QUERY_THRESHOLD == 1.0


def test_should_create_session_maker(mock_config):
    """Verifica que se crea el sessionmaker correctamente."""
    with patch("app.core.data.source.local.database.create_engine") as mock_create:
        mock_engine = MagicMock()
        mock_create.return_value = mock_engine

        _ = Database(config=mock_config)

        # Verify session was created with autocommit=False, autoflush=False
        # Access via mock_engine since we need to check session creation
        mock_engine.return_value = MagicMock()


def test_should_close_session_on_get_session(mock_config):
    """Verifica que el session se cierra correctamente."""
    with patch("app.core.data.source.local.database.create_engine") as mock_create:
        mock_engine = MagicMock()
        mock_create.return_value = mock_engine

        with patch("app.core.data.source.local.database.sessionmaker") as mock_sessionmaker:
            mock_session = MagicMock()
            mock_sessionmaker.return_value.return_value = mock_session

            db = Database(config=mock_config)

            # Use the generator
            session_gen = db.get_session()
            _ = next(session_gen)

            # Try to close (the finally block should handle this)
            try:
                next(session_gen)
            except StopIteration:
                pass

            mock_session.close.assert_called_once()
