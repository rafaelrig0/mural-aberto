import logging.config

from alembic import context
from sqlalchemy import create_engine, pool

# Importar os models é o que registra as tabelas no Base.metadata.
import app.models  # noqa: F401
from app.core.config import get_settings
from app.core.database import Base

if context.config.config_file_name is not None:
    logging.config.fileConfig(context.config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    engine = create_engine(
        get_settings().database_url,
        poolclass=pool.NullPool,
        connect_args={"prepare_threshold": None},
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
