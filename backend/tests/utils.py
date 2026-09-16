"""Helpers compartilhados pela suíte de testes."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.enums import RoleEnum
from app.models.usuario import Usuario


def make_user(
    db: Session,
    *,
    email: str,
    role: RoleEnum,
    password: str = "SenhaForte123!",
    full_name: str = "Usuario de Teste",
    unidade_id: int | None = None,
    is_active: bool = True,
) -> Usuario:
    user = Usuario(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        unidade_id=unidade_id,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header(user: Usuario) -> dict[str, str]:
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}
