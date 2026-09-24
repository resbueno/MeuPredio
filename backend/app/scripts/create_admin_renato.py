"""Cria (idempotente) o usuário administrador temporário pedido por Renato.

ATENÇÃO: este script é de uso pontual - depois de usado, desative o usuário
(is_active=False) ou remova este arquivo. Login usa e-mail, não "usuário";
como "renato.bueno" não é um e-mail válido, foi criado o e-mail abaixo.

Uso:
    cd backend
    python -m app.scripts.create_admin_renato
"""
from __future__ import annotations

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.enums import RoleEnum
from app.models.usuario import Usuario

EMAIL = "renato.bueno@meupredio.com"
SENHA = "Bel@!2026"
NOME = "Renato Bueno"


def main() -> None:
    db = SessionLocal()
    try:
        existente = (
            db.query(Usuario)
            .filter(Usuario.email == EMAIL, Usuario.predio_id.is_(None))
            .first()
        )
        if existente is not None:
            print(f"Usuario administrador '{EMAIL}' ja existe. Nada a fazer.")
            return

        admin = Usuario(
            email=EMAIL,
            hashed_password=hash_password(SENHA),
            full_name=NOME,
            role=RoleEnum.ADMINISTRADOR,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print(f"Usuario administrador '{EMAIL}' criado com sucesso.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
