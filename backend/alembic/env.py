from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Garante que todos os modelos estejam registrados em Base.metadata antes do
# autogenerate, e reaproveita a mesma configuração (DATABASE_URL) usada pela
# aplicação em runtime — nada de URL duplicada/hardcoded aqui.
from app.core.config import get_settings
from app.core.database import Base
import app.models  # noqa: F401  (registra os modelos em Base.metadata)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
# So aplica o default de settings.DATABASE_URL se quem chamou o Alembic (CLI
# `alembic upgrade`, ou testes via AlembicConfig.set_main_option) NAO tiver
# passado uma URL explicita. Sobrescrever incondicionalmente aqui ja causou
# um incidente real: a suite de testes configura sqlalchemy.url para o banco
# de teste isolado, mas essa linha ignorava isso e forcava DATABASE_URL de
# producao/homologacao - o "downgrade" de teardown dos testes rodou contra o
# banco real e apagou os dados de homologacao.
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
