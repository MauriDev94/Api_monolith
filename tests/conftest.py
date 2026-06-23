import os
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Desactiva el rate limiting por defecto en la suite: el TestClient comparte IP y
# acumularía estado entre tests. Los tests de rate limiting inyectan un limiter real.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")


@pytest.fixture(scope="session")
def _postgres_engine() -> Generator[Engine, None, None]:
    """Levanta un Postgres efímero (testcontainers) y corre las migraciones Alembic REALES.

    Usar el mismo motor que producción (Postgres) y aplicar `alembic upgrade head`
    en vez de `metadata.create_all` cierra el gap que escondía drift de esquema
    (p.ej. una columna declarada en el modelo pero sin migración que la cree).
    """
    from alembic import command
    from alembic.config import Config
    from testcontainers.postgres import PostgresContainer

    # Ryuk (el reaper de testcontainers) suele fallar el mapeo de puerto en Docker/Windows.
    # El context manager `with` ya detiene el contenedor al salir, así que es seguro desactivarlo.
    os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")

    with PostgresContainer("postgres:16-alpine") as postgres:
        url = postgres.get_connection_url()  # postgresql+psycopg2://test:test@host:port/test

        previous_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = url  # consumido por app/.../alembic/env.py
        try:
            command.upgrade(Config("alembic.ini"), "head")
            engine = create_engine(url)
            try:
                yield engine
            finally:
                engine.dispose()
        finally:
            if previous_url is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = previous_url


@pytest.fixture
def db_session(_postgres_engine: Engine) -> Generator[Session, None, None]:
    """Entrega una sesión aislada por test; limpia todas las tablas al terminar."""
    session_local = sessionmaker(bind=_postgres_engine, autocommit=False, autoflush=False)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
        _truncate_all_tables(_postgres_engine)


def _truncate_all_tables(engine: Engine) -> None:
    """Vacía todas las tablas de la app (preserva alembic_version) para aislar cada test."""
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        )
        tables = [row[0] for row in rows]
        if tables:
            joined = ", ".join(f'"{name}"' for name in tables)
            conn.execute(text(f"TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE"))


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Clasifica automáticamente los tests por alcance para no duplicar marcadores."""
    from pathlib import Path

    for item in items:
        path = Path(str(item.fspath)).as_posix()

        if "/tests/e2e/" in path:
            item.add_marker(pytest.mark.e2e)
            continue

        if (
            "/tests/core/exceptions/" in path
            or "/tests/core/data/" in path
            or (
                "/tests/features/" in path
                and ("/infrastructure/repositories/" in path or "/presentation/" in path)
            )
        ):
            item.add_marker(pytest.mark.integration)
            continue

        item.add_marker(pytest.mark.unit)
