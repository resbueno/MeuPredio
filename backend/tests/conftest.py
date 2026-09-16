from __future__ import annotations

import os
from pathlib import Path

# Precisa acontecer ANTES de qualquer import de app.* — garante que
# app.core.config.get_settings() não exija um .env configurado manualmente
# só para rodar a suíte de testes (ver validação em Settings/get_settings).
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "chave-de-teste-nao-usar-em-producao-" * 2)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config as AlembicConfig  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.dependencies import get_db  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
settings = get_settings()
TEST_DATABASE_URL = settings.sqlalchemy_database_url_test


@pytest.fixture(scope="session")
def _migrated_test_db():
    """Aplica todas as migrations Alembic (incluindo o trigger de
    imutabilidade da auditoria) no banco de teste, uma vez por sessão de
    testes. Usa o mesmo caminho de migration que roda em produção — a suíte
    testa o schema real, não um `create_all()` simplificado."""
    alembic_cfg = AlembicConfig(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")
    yield
    command.downgrade(alembic_cfg, "base")


@pytest.fixture(scope="session")
def engine(_migrated_test_db):
    eng = create_engine(TEST_DATABASE_URL, future=True)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine) -> Session:
    """Uma sessão isolada por teste: abre uma transação externa e, dentro
    dela, uma SAVEPOINT que é reiniciada a cada `commit()` feito pelo código
    de aplicação (routers chamam `db.commit()` normalmente). Ao final do
    teste a transação externa sempre sofre rollback — nenhum teste enxerga
    dados de outro, sem precisar truncar tabelas manualmente.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = TestingSessionLocal()
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
