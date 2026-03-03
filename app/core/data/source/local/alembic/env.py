from logging.config import fileConfig
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# load the .env file
load_dotenv(".env")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# get the DB_URL from the .env file
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL is not set in the .env file")

# import the base
from app.core.data.source.local.sql_alchemy_base import SqlAlchemyBase
from app.features.users.infrastructure.models.user_model import UserModel  # type: ignore
from app.features.todos.infrastructure.models.todo_model import TodoModel  # type: ignore


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SqlAlchemyBase.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # create engine
    engine = create_engine(database_url, poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
