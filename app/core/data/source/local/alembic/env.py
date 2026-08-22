import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool

# load the .env file
load_dotenv(".env")

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Priority: DATABASE_URL (Render managed DB) > individual vars (local dev)
database_url = os.getenv("DATABASE_URL")
if not database_url:
    # Fallback: build from individual vars for local development
    from app.core.config.env_config import EnvConfig

    _cfg = EnvConfig()
    database_url = (
        f"postgresql+psycopg2://{_cfg.db_user}:{_cfg.db_password}"
        f"@{_cfg.db_host}:{_cfg.db_port}/{_cfg.db_name}"
    )

# Render delivers postgres:// — SQLAlchemy 2.0 requires postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# import the base
from app.core.data.source.local.sql_alchemy_base import SqlAlchemyBase

# Importar TODOS los modelos para que se registren en SqlAlchemyBase.metadata.
# Sin esto, target_metadata queda vacío y autogenerate/`alembic check` no detectan
# drift (la causa de fondo del bug O1: due_date en el modelo sin migración).
from app.features.auth.infrastructure.models.otp_model import OtpModel  # noqa: F401
from app.features.auth.infrastructure.models.refresh_token_model import (  # noqa: F401
    RefreshTokenModel,
)
from app.features.todos.infrastructure.models.todo_model import TodoModel  # noqa: F401
from app.features.users.infrastructure.models.user_model import UserModel  # noqa: F401

# add your model's MetaData object here for 'autogenerate' support
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
