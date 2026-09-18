from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.models.aviso_mural import AvisoMural
from app.models.enums import RoleEnum, TipoAvisoMuralEnum
from app.models.usuario import Usuario
from app.schemas.aviso_mural import AvisoMuralAtualizar, AvisoMuralCreate, AvisoMuralRead

router = APIRouter(prefix="/avisos-mural", tags=["avisos-mural"])

# Quem publica/edita/remove QUALQUER aviso tipo 'condominio', não só o
# próprio - é um mural de gestão coletiva, não de autoria individual.
_GESTAO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _aviso_ou_404(db: Session, aviso_id: int, current_user: Usuario) -> AvisoMural:
    aviso = db.get(AvisoMural, aviso_id)
    if aviso is None or aviso.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso não encontrado.")
    if current_user.role != RoleEnum.ADMINISTRADOR and aviso.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso não encontrado.")
    return aviso


def _exigir_pode_editar(aviso: AvisoMural, current_user: Usuario) -> None:
    if aviso.tipo == TipoAvisoMuralEnum.CONDOMINIO:
        if not (current_user.roles_efetivos & set(_GESTAO)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Só síndico ou administrador edita um aviso de condomínio.",
            )
        return
    if aviso.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só quem publicou o anúncio pode editá-lo.",
        )


def _exigir_pode_remover(aviso: AvisoMural, current_user: Usuario) -> None:
    if aviso.tipo == TipoAvisoMuralEnum.CONDOMINIO:
        if not (current_user.roles_efetivos & set(_GESTAO)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Só síndico ou administrador remove um aviso de condomínio.",
            )
        return
    # Anuncio: o proprio autor remove, OU a gestao modera (spec: "admin e
    # sindico podem remover anuncios de venda").
    if aviso.created_by != current_user.id and not (current_user.roles_efetivos & set(_GESTAO)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para remover este anúncio.",
        )


@router.post("", response_model=AvisoMuralRead, status_code=status.HTTP_201_CREATED)
def criar_aviso_mural(
    payload: AvisoMuralCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> AvisoMural:
    if payload.tipo == TipoAvisoMuralEnum.CONDOMINIO and not (current_user.roles_efetivos & set(_GESTAO)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só síndico ou administrador publica um aviso de condomínio.",
        )

    predio_id = resolver_predio_id(current_user, payload.predio_id)
    aviso = AvisoMural(
        predio_id=predio_id,
        tipo=payload.tipo,
        titulo=payload.titulo,
        descricao=payload.descricao,
        preco=payload.preco,
        created_by=current_user.id,
    )
    db.add(aviso)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="avisos_mural",
        entidade_id=aviso.id,
        dados_depois=model_to_audit_dict(aviso),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(aviso)
    return aviso


@router.get("", response_model=list[AvisoMuralRead])
def listar_avisos_mural(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
    tipo: TipoAvisoMuralEnum | None = None,
) -> list[AvisoMural]:
    query = db.query(AvisoMural).filter(AvisoMural.deleted_at.is_(None))
    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id is not None:
            query = query.filter(AvisoMural.predio_id == predio_id)
    else:
        query = query.filter(AvisoMural.predio_id == current_user.predio_id)
    if tipo is not None:
        query = query.filter(AvisoMural.tipo == tipo)
    return query.order_by(AvisoMural.created_at.desc()).all()


@router.patch("/{aviso_id}", response_model=AvisoMuralRead)
def atualizar_aviso_mural(
    aviso_id: int,
    payload: AvisoMuralAtualizar,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> AvisoMural:
    aviso = _aviso_ou_404(db, aviso_id, current_user)
    _exigir_pode_editar(aviso, current_user)

    campos_enviados = payload.model_dump(exclude_unset=True)
    dados_antes = model_to_audit_dict(aviso)
    for campo in ("titulo", "descricao", "preco"):
        if campo in campos_enviados:
            setattr(aviso, campo, campos_enviados[campo])
    db.add(aviso)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="avisos_mural",
        entidade_id=aviso.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(aviso),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(aviso)
    return aviso


@router.delete("/{aviso_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_aviso_mural(
    aviso_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> None:
    aviso = _aviso_ou_404(db, aviso_id, current_user)
    _exigir_pode_remover(aviso, current_user)

    dados_antes = model_to_audit_dict(aviso)
    aviso.deleted_at = datetime.now(timezone.utc)
    db.add(aviso)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="SOFT_DELETE",
        entidade="avisos_mural",
        entidade_id=aviso.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(aviso),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None
