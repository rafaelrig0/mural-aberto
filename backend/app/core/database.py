import enum
from collections.abc import Iterator
from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, Enum, MetaData, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column, sessionmaker

from app.core.config import get_settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# prepare_threshold=None desativa prepared statements, necessário se usar o
# transaction pooler do Supabase; é inofensivo nas demais conexões.
engine = create_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    connect_args={"prepare_threshold": None},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


CreatedAt = Annotated[
    datetime,
    mapped_column(DateTime(timezone=True), server_default=func.now()),
]


def enum_column(enum_cls: type[enum.Enum]) -> Enum:
    """Enum guardado como texto (VARCHAR + CHECK), não como enum nativo do Postgres.

    Enums nativos são difíceis de alterar em migrações; texto com CHECK
    dá a mesma integridade com evolução muito mais simples.
    """
    return Enum(
        enum_cls,
        name=enum_cls.__name__.lower(),
        native_enum=False,
        create_constraint=True,
        length=20,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )


def get_db() -> Iterator[Session]:
    """Uma sessão por requisição. Não há commit automático: cada service faz o seu."""
    with SessionLocal() as session:
        yield session
