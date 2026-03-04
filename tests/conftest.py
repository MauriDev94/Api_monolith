from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.data.source.local.sql_alchemy_base import SqlAlchemyBase
from app.features.todos.infrastructure.models.todo_model import TodoModel  # noqa: F401
from app.features.users.infrastructure.models.user_model import UserModel  # noqa: F401


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide an isolated in-memory database session per test."""
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
