import os
import time
from collections.abc import Generator

from loguru import logger
from sqlalchemy import event
from sqlalchemy.engine import URL, create_engine
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import Session, sessionmaker

from app.core.config.env_config import EnvConfig
from app.core.data.source.local.sql_alchemy_base import SqlAlchemyBase


class Database:
    """Database factory that builds SQLAlchemy engine and sessions."""

    # Threshold for slow query logging in seconds
    SLOW_QUERY_THRESHOLD = 1.0

    def __init__(self, config: EnvConfig):
        """Initialize connection resources from environment configuration.

        Priority: DATABASE_URL env var (Render managed DB) > individual vars (local dev).
        Render provides postgres:// — SQLAlchemy 2.0 requires postgresql://, fixed inline.
        """
        raw_url = os.getenv("DATABASE_URL")
        if raw_url:
            # Render delivers postgres:// — SQLAlchemy 2.0 requires postgresql://
            if raw_url.startswith("postgres://"):
                raw_url = raw_url.replace("postgres://", "postgresql://", 1)
            self.engine = create_engine(raw_url, echo=False, pool_pre_ping=True, pool_recycle=300)
        else:
            missing = [
                name
                for name, value in (
                    ("db_user", config.db_user),
                    ("db_password", config.db_password),
                    ("db_name", config.db_name),
                    ("db_port", config.db_port),
                    ("db_host", config.db_host),
                )
                if value is None
            ]
            if missing:
                raise ValueError(
                    "Database not configured: set DATABASE_URL, or the missing vars: "
                    + ", ".join(missing)
                )
            url = URL.create(
                drivername="postgresql+psycopg2",
                username=config.db_user,
                password=config.db_password,
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
            )
            self.engine = create_engine(url, echo=False, pool_pre_ping=True, pool_recycle=300)
        self.session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.SqlAlchemyBase = SqlAlchemyBase

        # Attach slow query logging
        self._setup_slow_query_logging()

    def _setup_slow_query_logging(self) -> None:
        """Register event listeners for slow query detection."""

        @event.listens_for(self.engine, "before_cursor_execute")
        # SQLAlchemy event signatures are dynamic: parameters/context types
        # depend on the dialect and driver, and mypy cannot infer them. We
        # type only what we use (DBAPIConnection) and silence the rest.
        def before_execute(  # type: ignore[no-untyped-def]
            conn: DBAPIConnection,
            cursor,
            statement,
            parameters,
            context,
            executemany,
        ):
            conn.info.setdefault("query_start_time", []).append(time.monotonic())

        @event.listens_for(self.engine, "after_cursor_execute")
        # Same rationale as before_execute — see comment above.
        def after_execute(  # type: ignore[no-untyped-def]
            conn: DBAPIConnection,
            cursor,
            statement,
            parameters,
            context,
            executemany,
        ):
            total_time = (
                time.monotonic() - conn.info.pop("query_start_time", [time.monotonic()])[-1]
            )
            if total_time > self.SLOW_QUERY_THRESHOLD:
                logger.warning(
                    f"SLOW QUERY ({total_time:.3f}s): {statement[:200]}",
                    extra={"slow_query": True, "duration": total_time},
                )

    def get_session(self) -> Generator[Session, None, None]:
        """Yield a session and guarantee proper close at the end."""
        db: Session = self.session()
        try:
            yield db
        finally:
            db.close()
