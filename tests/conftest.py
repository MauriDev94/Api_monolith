from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.data.source.local.sql_alchemy_base import SqlAlchemyBase
from app.features.todos.infrastructure.models.todo_model import TodoModel  # noqa: F401
from app.features.users.infrastructure.models.user_model import UserModel  # noqa: F401


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Entrega una sesion de base de datos en memoria aislada por cada test."""
    # Creates a fresh schema for every test, avoiding state leakage.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        SqlAlchemyBase.metadata.drop_all(bind=engine)
        engine.dispose()


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Clasifica automaticamente los tests por alcance para evitar duplicar marcadores en cada archivo."""
    for item in items:
        path = Path(str(item.fspath)).as_posix()

        if "/tests/e2e/" in path:
            item.add_marker(pytest.mark.e2e)
            continue

        if (
            "/tests/core/exceptions/" in path
            or "/tests/features/" in path
            and (
                "/infrastructure/repositories/" in path
                or "/presentation/" in path
            )
        ):
            item.add_marker(pytest.mark.integration)
            continue

        item.add_marker(pytest.mark.unit)
