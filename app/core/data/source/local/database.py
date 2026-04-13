import time
from collections.abc import Generator

from loguru import logger
from sqlalchemy.engine import URL, create_engine
from sqlalchemy.engine.events import DBAPIConnection
from sqlalchemy.orm import Session, sessionmaker

from app.core.config.env_config import EnvConfig
from app.core.data.source.local.sql_alchemy_base import SqlAlchemyBase


class Database:
    """Database factory that builds SQLAlchemy engine and sessions."""

    # Threshold for slow query logging in seconds
    SLOW_QUERY_THRESHOLD = 1.0

    def __init__(self, config: EnvConfig):
        """Initialize connection resources from environment configuration."""
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=config.db_user,
            password=config.db_password,
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
        )
        self.engine = create_engine(url, echo=False)
        self.session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.SqlAlchemyBase = SqlAlchemyBase

        # Attach slow query logging
        self._setup_slow_query_logging()

    def _setup_slow_query_logging(self):
        """Register event listeners for slow query detection."""

        @self.engine.listen_for("before_cursor_execute")
        def before_execute(
            conn: DBAPIConnection, cursor, statement, parameters, context, executemany
        ):
            conn.info.setdefault("query_start_time", []).append(time.monotonic())

        @self.engine.listen_for("after_cursor_execute")
        def after_execute(
            conn: DBAPIConnection, cursor, statement, parameters, context, executemany
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
