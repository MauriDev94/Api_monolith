from typing import Generator
from sqlalchemy.orm import Session
from app.core.data.source.local.database import Database
from app.core.providers.env_config import get_env_config


def get_db_session() -> Generator[Session, None, None]:
    database = Database(get_env_config())
    yield from database.get_session()
