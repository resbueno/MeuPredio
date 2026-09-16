from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_current_user, get_db, require_role
from app.core.security import hash_password
from app.models.enums import RoleEnum
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# Papéis com privilégios de gestão de usuários (administração do condomínio).
_GESTORES = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _usuario_ou_404(db: Session, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")
    return usuario


def _autorizar_acesso_ou_self(current_user: Usuario, usuario_id: int) -> None:
    if current_user.role not in _GESTORES and current_user.id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce so pode acessar o seu proprio cadastro.",
        )


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    payload: UsuarioCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTORES)),
) -> Usuario:
    if payload.role == RoleEnum.ADMINISTRADOR and current_user.role != RoleEnum.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente um administrador pode criar outro administrador.",
        )

    email_em_uso = (
        db.query(Usuario)
        .filter(Usuario.email == payload.email, Usuario.deleted_at.is_(None))
        .first()
    )
    if email_em_uso is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail ja cadastrado.")

    usuario = Usuario(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        unidade_id=payload.unidade_id,
        is_active=True,
        created_by=current_user.id,
    )
    db.add(usuario)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="usuarios",
        entidade_id=usuario.id,
        dados_depois=model_to_audit_dict(usuario),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("", response_model=list[UsuarioRead])
def listar_usuarios(
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(require_role(*_GESTORES)),
    incluir_inativos: bool = False,
) -> list[Usuario]:
    query = db.query(Usuario)
    if not incluir_inativos:
        query = query.filter(Usuario.deleted_at.is_(None))
    return query.order_by(Usuario.id).all()


@router.get("/{usuario_id}", response_model=UsuarioRead)
def obter_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    _autorizar_acesso_ou_self(current_user, usuario_id)
    usuario = _usuario_ou_404(db, usuario_id)
    if usuario.deleted_at is not None and current_user.role not in _GESTORES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario nao encontrado.")
    return usuario


@router.patch("/{usuario_id}", response_model=UsuarioRead)
def atualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    _autorizar_acesso_ou_self(current_user, usuario_id)
    usuario = _usuario_ou_404(db, usuario_id)

    is_gestor = current_user.role in _GESTORES
    campos_enviados = payload.model_dump(exclude_unset=True)

    campos_restritos_a_gestor = {"role", "is_active", "unidade_id"}
    if not is_gestor and campos_restritos_a_gestor.intersection(campos_enviados):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Voce nao tem permissao para alterar este campo.",
        )

    if "role" in campos_enviados and campos_enviados["role"] == RoleEnum.ADMINISTRADOR:
        if current_user.role != RoleEnum.ADMINISTRADOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Somente um administrador pode conceder o papel de administrador.",
            )

    dados_antes = model_to_audit_dict(usuario)

    if "full_name" in campos_enviados:
        usuario.full_name = campos_enviados["full_name"]
    if "unidade_id" in campos_enviados:
        usuario.unidade_id = campos_enviados["unidade_id"]
    if "role" in campos_enviados:
        usuario.role = campos_enviados["role"]
    if "is_active" in campos_enviados:
        usuario.is_active = campos_enviados["is_active"]
    if campos_enviados.get("password"):
        usuario.hashed_password = hash_password(campos_enviados["password"])

    db.add(usuario)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="usuarios",
        entidade_id=usuario.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(usuario),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTORES)),
) -> None:
    """Soft-delete: marca `deleted_at` e desativa o usuário. Nunca faz DELETE
    físico — preserva histórico para auditoria e possível restauração."""
    usuario = _usuario_ou_404(db, usuario_id)
    if usuario.deleted_at is not None:
        return None

    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voce nao pode remover o proprio usuario.",
        )

    dados_antes = model_to_audit_dict(usuario)
    usuario.deleted_at = datetime.now(timezone.utc)
    usuario.is_active = False
    db.add(usuario)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="SOFT_DELETE",
        entidade="usuarios",
        entidade_id=usuario.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(usuario),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None


@router.post("/{usuario_id}/anonimizar", response_model=UsuarioRead)
def anonimizar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR)),
) -> Usuario:
    """Anonimização para fins de LGPD: substitui os dados pessoais do usuário
    por valores não identificáveis, preservando a linha (e seu histórico de
    auditoria associado) para fins contábeis/legais, sem reter dados pessoais
    reais. Ação restrita a ADMINISTRADOR e irreversível.
    """
    usuario = _usuario_ou_404(db, usuario_id)
    if usuario.anonymized_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuario ja foi anonimizado.")

    dados_antes = model_to_audit_dict(usuario)

    usuario.email = f"anonimizado-{usuario.id}@meupredio.invalid"
    usuario.full_name = "Usuario Anonimizado"
    # Sobrescreve o hash com um valor aleatório e descartado (não é
    # reversível para nenhuma senha real) para invalidar qualquer credencial
    # antiga, em defesa em profundidade.
    usuario.hashed_password = hash_password(secrets.token_urlsafe(32))
    usuario.consent_lgpd_accepted_at = None
    usuario.is_active = False
    usuario.deleted_at = usuario.deleted_at or datetime.now(timezone.utc)
    usuario.anonymized_at = datetime.now(timezone.utc)

    db.add(usuario)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="ANONYMIZE",
        entidade="usuarios",
        entidade_id=usuario.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(usuario),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(usuario)
    return usuario
