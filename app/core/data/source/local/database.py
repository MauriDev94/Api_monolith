from typing import Generator
from sqlalchemy.engine import URL, create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config.env_config import EnvConfig
from app.core.data.source.local.sql_alchemy_base import SqlAlchemyBase


class Database:
    def __init__(self, config: EnvConfig):
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=config.db_user,
            password=config.db_password,
            host=config.db_host,
            port=config.db_port,
            database=config.db_name,
        )
        self.engine = create_engine(url, echo=True)
        self.session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self.SqlAlchemyBase = SqlAlchemyBase

    def get_session(self) -> Generator[Session, None, None]:
        db: Session = self.session()
        try:
            yield db
        finally:
            db.close()
