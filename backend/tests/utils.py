"""Helpers compartilhados pela suíte de testes."""
from __future__ import annotations

import itertools

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.enums import RoleEnum
from app.models.predio import Predio
from app.models.unidade import Unidade
from app.models.usuario import Usuario

# Contador monotônico em processo: cada chamada a make_predio() sem cep/numero
# explícitos gera um par único, mesmo entre testes diferentes (cada teste usa
# uma transação isolada que sofre rollback, mas o contador em si não - o que
# é exatamente o que queremos, para nunca colidir com a UniqueConstraint
# (cep, numero) mesmo rodando muitos testes na mesma sessão).
_contador_predio = itertools.count(1)
# Contador dedicado para unidades AUTO-criadas por make_user() (quando o
# chamador não passa `unidades` explicitamente) - nunca "A"/"101" fixo, para
# não colidir com uma unidade que o próprio teste já tenha criado no mesmo
# prédio via make_unidade() com esses mesmos valores default.
_contador_unidade_auto = itertools.count(1)


def make_predio(db: Session, *, nome: str = "Predio de Teste", cep: str | None = None, numero: str | None = None) -> Predio:
    n = next(_contador_predio)
    predio = Predio(
        nome=nome,
        cep=cep or f"{10000000 + n:08d}",
        numero=numero or str(n),
        cidade="Sao Paulo",
        uf="SP",
    )
    db.add(predio)
    db.commit()
    db.refresh(predio)
    return predio


def make_unidade(db: Session, predio: Predio, *, bloco: str = "A", numero: str = "101") -> Unidade:
    unidade = Unidade(predio_id=predio.id, bloco=bloco, numero=numero)
    db.add(unidade)
    db.commit()
    db.refresh(unidade)
    return unidade


def make_user(
    db: Session,
    *,
    email: str,
    role: RoleEnum,
    password: str = "SenhaForte123!",
    full_name: str = "Usuario de Teste",
    predio: Predio | None = None,
    unidades: list[Unidade] | None = None,
    is_active: bool = True,
) -> Usuario:
    """Cria um usuário de teste. Para qualquer papel exceto ADMINISTRADOR
    (que é global, sem prédio), exige vínculo com prédio+unidade(s) - se
    `predio`/`unidades` não forem passados explicitamente, cria um prédio e
    uma unidade novos e dedicados para este usuário (suficiente para testes
    que não precisam compartilhar prédio entre usuários; passe `predio`
    explicitamente quando o teste precisar de dois usuários no MESMO
    prédio - ver testes de multi-tenancy)."""
    predio_id: int | None = None
    unidade_objs: list[Unidade] = []

    if role != RoleEnum.ADMINISTRADOR:
        if predio is None:
            predio = make_predio(db)
        predio_id = predio.id
        if unidades is None:
            n = next(_contador_unidade_auto)
            unidades = [make_unidade(db, predio, bloco="AUTO", numero=str(n))]
        unidade_objs = unidades

    user = Usuario(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
        predio_id=predio_id,
        unidades=unidade_objs,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def auth_header(user: Usuario) -> dict[str, str]:
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


def login_form(email: str, password: str, predio_id: int | None = None) -> dict[str, str]:
    """Monta o corpo (form-urlencoded) de POST /auth/login. `predio_id`
    omitido = tentativa de login como administrador (ver routers/auth.py)."""
    form = {"username": email, "password": password}
    if predio_id is not None:
        form["predio_id"] = str(predio_id)
    return form
