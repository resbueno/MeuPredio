"""Engine, sessão e Base declarativa do SQLAlchemy 2.0."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os modelos ORM."""


def get_db_session() -> Generator[Session, None, None]:
    """Gera uma sessão de banco por request, garantindo o fechamento no final.

    Usada diretamente por `app.core.dependencies.get_db` (FastAPI Depends).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
