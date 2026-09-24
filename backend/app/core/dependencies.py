"""Dependencies FastAPI reutilizáveis: sessão de banco, usuário atual e RBAC."""
from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db_session
from app.core.security import decode_access_token
from app.models.enums import ModuloEnum, RoleEnum
from app.models.usuario import Usuario

# tokenUrl aponta para o endpoint de login — usado apenas para gerar a UI do
# Swagger ("Authorize"), a validação real acontece em decode_access_token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db() -> Generator[Session, None, None]:
    yield from get_db_session()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise credentials_exception from None

    subject = payload.get("sub")
    if subject is None:
        raise credentials_exception
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise credentials_exception from None

    user = db.get(Usuario, user_id)
    # Usuário inexistente, com soft-delete aplicado, ou desativado: trata como
    # não autenticado (nunca revela qual dessas condições ocorreu).
    if user is None or user.is_deleted or not user.is_active:
        raise credentials_exception

    return user


def resolver_predio_id(current_user: Usuario, predio_id_informado: int | None) -> int:
    """Multi-tenancy: decide qual `predio_id` vale para a operação atual.

    - ADMINISTRADOR (papel global, sem prédio): PRECISA informar
      explicitamente qual prédio, já que não tem um próprio.
    - Qualquer outro papel: o prédio é sempre o do próprio usuário logado,
      IGNORANDO qualquer predio_id que o cliente tente enviar - isolamento
      entre tenants nunca pode depender de o cliente "se comportar".
    """
    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id_informado is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Administrador precisa informar predio_id explicitamente.",
            )
        return predio_id_informado
    return current_user.predio_id  # type: ignore[return-value]


def require_role(*roles: RoleEnum):
    """Dependency factory de RBAC.

    Uso: `current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR))`.
    Sem papéis == qualquer usuário autenticado (equivalente a `get_current_user`).

    Compara contra `roles_efetivos` (papel principal + papéis adicionais,
    ver `Usuario.roles_efetivos`) - basta UM papel do usuário bater com um
    dos permitidos, já que a mesma pessoa pode acumular funções (ex.: um
    síndico que também é morador da própria unidade).
    """
    allowed = set(roles)

    def _dependency(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if allowed and not (current_user.roles_efetivos & allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para executar esta ação.",
            )
        return current_user

    return _dependency


def require_modulo(modulo: ModuloEnum):
    """Dependency factory de módulos opcionais por prédio.

    Uso: `dependencies=[Depends(require_modulo(ModuloEnum.FINANCEIRO))]` no
    `include_router` (ver app/main.py) - todo o router fica atrás do módulo.
    `ADMINISTRADOR` (papel global, sem prédio) sempre passa, já que gerencia
    a plataforma inteira, não um prédio específico."""

    def _dependency(current_user: Usuario = Depends(get_current_user)) -> Usuario:
        if current_user.role == RoleEnum.ADMINISTRADOR:
            return current_user
        predio = current_user.predio
        if predio is None or modulo.value not in predio.modulos_habilitados:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este módulo não está habilitado para o seu prédio.",
            )
        return current_user

    return _dependency
