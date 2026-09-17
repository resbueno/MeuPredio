"""Bootstrap idempotente do primeiro usuário Administrador.

Uso:
    python -m app.scripts.seed_admin

Lê FIRST_ADMIN_EMAIL / FIRST_ADMIN_PASSWORD / FIRST_ADMIN_FULL_NAME das
variáveis de ambiente (.env). Não faz nada (idempotente) se já existir um
usuário com esse e-mail — seguro para rodar em todo deploy/startup.
"""
from __future__ import annotations

import sys

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.enums import RoleEnum
from app.models.usuario import Usuario


def seed_admin() -> None:
    settings = get_settings()

    if not settings.FIRST_ADMIN_EMAIL or not settings.FIRST_ADMIN_PASSWORD:
        print(
            "FIRST_ADMIN_EMAIL/FIRST_ADMIN_PASSWORD nao configurados no .env; "
            "nenhum administrador foi criado.",
            file=sys.stderr,
        )
        return

    db = SessionLocal()
    try:
        # predio_id IS NULL: e-mail só é globalmente único entre
        # administradores (ver CheckConstraint/índices parciais em
        # Usuario) - sem esse filtro, poderíamos "encontrar" por engano um
        # morador/síndico de algum prédio com o mesmo e-mail coincidente.
        existing = (
            db.query(Usuario)
            .filter(Usuario.email == settings.FIRST_ADMIN_EMAIL, Usuario.predio_id.is_(None))
            .first()
        )
        if existing is not None:
            print(f"Usuario administrador '{settings.FIRST_ADMIN_EMAIL}' ja existe. Nada a fazer.")
            return

        admin = Usuario(
            email=settings.FIRST_ADMIN_EMAIL,
            hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
            full_name=settings.FIRST_ADMIN_FULL_NAME,
            role=RoleEnum.ADMINISTRADOR,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Usuario administrador '{settings.FIRST_ADMIN_EMAIL}' criado com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
