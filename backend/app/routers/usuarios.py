from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_current_user, get_db, require_role, resolver_predio_id
from app.core.security import hash_password
from app.models.enums import RoleEnum
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.models.usuario_papel_extra import UsuarioPapelExtra
from app.schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# Papéis com privilégios de gestão de usuários (administração do condomínio).
_GESTORES = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _usuario_ou_404(db: Session, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return usuario


def _autorizar_acesso_ou_self(current_user: Usuario, alvo: Usuario) -> None:
    """Combina a regra "self ou gestor" (já existia) com isolamento
    multi-tenant: um síndico NUNCA acessa usuário de outro prédio - some
    (404), sem confirmar que o usuário existe em outro tenant."""
    if current_user.id == alvo.id:
        return
    if not (current_user.roles_efetivos & set(_GESTORES)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar o seu próprio cadastro.",
        )
    if current_user.role != RoleEnum.ADMINISTRADOR and current_user.predio_id != alvo.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")


def _validar_unidades(db: Session, unidade_ids: list[int], predio_id: int) -> list[Unidade]:
    if not unidade_ids:
        return []
    unidades = (
        db.query(Unidade)
        .filter(
            Unidade.id.in_(unidade_ids),
            Unidade.predio_id == predio_id,
            Unidade.deleted_at.is_(None),
        )
        .all()
    )
    if len(unidades) != len(set(unidade_ids)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uma ou mais unidades informadas não existem neste prédio.",
        )
    return unidades


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    payload: UsuarioCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTORES)),
) -> Usuario:
    if payload.role == RoleEnum.ADMINISTRADOR:
        if current_user.role != RoleEnum.ADMINISTRADOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Somente um administrador pode criar outro administrador.",
            )
        predio_id: int | None = None
        unidades: list[Unidade] = []
    else:
        predio_id = resolver_predio_id(current_user, payload.predio_id)
        unidades = _validar_unidades(db, payload.unidade_ids, predio_id)

    email_em_uso = (
        db.query(Usuario)
        .filter(
            Usuario.email == payload.email,
            Usuario.predio_id == predio_id,
            Usuario.deleted_at.is_(None),
        )
        .first()
    )
    if email_em_uso is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado.")

    usuario = Usuario(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        predio_id=predio_id,
        unidades=unidades,
        papeis_extra=[
            UsuarioPapelExtra(role=papel, created_by=current_user.id)
            for papel in payload.papeis_extra
        ],
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
    current_user: Usuario = Depends(require_role(*_GESTORES)),
    predio_id: int | None = None,
    incluir_inativos: bool = False,
) -> list[Usuario]:
    query = db.query(Usuario)
    if not incluir_inativos:
        query = query.filter(Usuario.deleted_at.is_(None))

    if current_user.role == RoleEnum.ADMINISTRADOR:
        # Administrador enxerga a plataforma toda; predio_id aqui é um
        # filtro opcional, não uma obrigação (diferente de criar recursos,
        # onde ele precisa dizer para qual prédio é).
        if predio_id is not None:
            query = query.filter(Usuario.predio_id == predio_id)
    else:
        # Síndico: sempre restrito ao próprio prédio, ignorando qualquer
        # predio_id que tente passar via query string.
        query = query.filter(Usuario.predio_id == current_user.predio_id)

    return query.order_by(Usuario.id).all()


@router.get("/{usuario_id}", response_model=UsuarioRead)
def obter_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    usuario = _usuario_ou_404(db, usuario_id)
    _autorizar_acesso_ou_self(current_user, usuario)
    if usuario.deleted_at is not None and not (current_user.roles_efetivos & set(_GESTORES)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return usuario


@router.patch("/{usuario_id}", response_model=UsuarioRead)
def atualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    usuario = _usuario_ou_404(db, usuario_id)
    _autorizar_acesso_ou_self(current_user, usuario)

    is_gestor = bool(current_user.roles_efetivos & set(_GESTORES))
    campos_enviados = payload.model_dump(exclude_unset=True)

    campos_restritos_a_gestor = {"role", "is_active", "unidade_ids", "papeis_extra"}
    if not is_gestor and campos_restritos_a_gestor.intersection(campos_enviados):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para alterar este campo.",
        )

    novo_role = campos_enviados.get("role", usuario.role)
    if "role" in campos_enviados and novo_role == RoleEnum.ADMINISTRADOR:
        if current_user.role != RoleEnum.ADMINISTRADOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Somente um administrador pode conceder o papel de administrador.",
            )
    if "role" in campos_enviados and usuario.role == RoleEnum.ADMINISTRADOR and novo_role != RoleEnum.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível rebaixar um administrador para um papel vinculado a prédio por aqui.",
        )
    if "papeis_extra" in campos_enviados:
        novos_papeis_extra = campos_enviados["papeis_extra"]
        if novo_role == RoleEnum.ADMINISTRADOR and novos_papeis_extra:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrador é um papel global e não acumula outros papéis.",
            )
        if novo_role in novos_papeis_extra:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O papel principal não pode se repetir na lista de papéis adicionais.",
            )

    dados_antes = model_to_audit_dict(usuario)

    if "full_name" in campos_enviados:
        usuario.full_name = campos_enviados["full_name"]
    if "unidade_ids" in campos_enviados:
        if usuario.role == RoleEnum.ADMINISTRADOR or novo_role == RoleEnum.ADMINISTRADOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrador não pode estar vinculado a unidades.",
            )
        usuario.unidades = _validar_unidades(db, campos_enviados["unidade_ids"], usuario.predio_id)
    if "role" in campos_enviados:
        usuario.role = campos_enviados["role"]
    if "papeis_extra" in campos_enviados:
        usuario.papeis_extra = [
            UsuarioPapelExtra(role=papel, created_by=current_user.id)
            for papel in campos_enviados["papeis_extra"]
        ]
    if "is_active" in campos_enviados:
        usuario.is_active = campos_enviados["is_active"]
    if campos_enviados.get("password"):
        usuario.hashed_password = hash_password(campos_enviados["password"])
        # Revoga qualquer JWT emitido antes desta troca (ver
        # get_current_user) - importante sobretudo quando é outra pessoa
        # (síndico/administrador) trocando a senha de alguém por suspeita de
        # conta comprometida: sem isto, um token já vazado continuaria
        # válido até expirar por conta própria.
        usuario.senha_alterada_em = datetime.now(timezone.utc)

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


@router.post("/{usuario_id}/consentimento-lgpd/aceitar", response_model=UsuarioRead)
def aceitar_consentimento_lgpd(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Consentimento LGPD é sempre pessoal - nem a gestão aceita/revoga em
    nome de outra pessoa, só o próprio titular dos dados."""
    usuario = _usuario_ou_404(db, usuario_id)
    if current_user.id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só você pode aceitar o seu próprio consentimento LGPD.",
        )

    dados_antes = model_to_audit_dict(usuario)
    usuario.consent_lgpd_accepted_at = datetime.now(timezone.utc)
    db.add(usuario)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="LGPD_CONSENT_ACCEPT",
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


@router.post("/{usuario_id}/consentimento-lgpd/revogar", response_model=UsuarioRead)
def revogar_consentimento_lgpd(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    usuario = _usuario_ou_404(db, usuario_id)
    if current_user.id != usuario.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só você pode revogar o seu próprio consentimento LGPD.",
        )

    dados_antes = model_to_audit_dict(usuario)
    usuario.consent_lgpd_accepted_at = None
    db.add(usuario)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="LGPD_CONSENT_REVOKE",
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
    if current_user.role != RoleEnum.ADMINISTRADOR and current_user.predio_id != usuario.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    if usuario.deleted_at is not None:
        return None

    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode remover o próprio usuário.",
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
    reais. Ação restrita a ADMINISTRADOR (papel global da plataforma, atua
    entre prédios para fins de compliance) e irreversível.
    """
    usuario = _usuario_ou_404(db, usuario_id)
    if usuario.anonymized_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Usuário já foi anonimizado.")

    dados_antes = model_to_audit_dict(usuario)

    usuario.email = f"anonimizado-{usuario.id}@meupredio.invalid"
    usuario.full_name = "Usuario Anonimizado"
    # Sobrescreve o hash com um valor aleatório e descartado (não é
    # reversível para nenhuma senha real) para invalidar qualquer credencial
    # antiga, em defesa em profundidade.
    usuario.hashed_password = hash_password(secrets.token_urlsafe(32))
    usuario.senha_alterada_em = datetime.now(timezone.utc)
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
