from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.core.notificacoes import ids_usuarios_da_unidade, notificar_usuarios
from app.models.enums import RoleEnum, TipoNotificacaoEnum
from app.models.entrega import Entrega
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.entrega import EntregaCreate, EntregaRead

router = APIRouter(prefix="/entregas", tags=["entregas"])

# Quem registra uma entrega na portaria - o zelador é quem normalmente
# recebe, mas síndico/administrador também podem lançar.
_REGISTRADORES = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO, RoleEnum.ZELADOR)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _entrega_ou_404(db: Session, entrega_id: int, current_user: Usuario) -> Entrega:
    entrega = db.get(Entrega, entrega_id)
    if entrega is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega não encontrada.")
    if current_user.role != RoleEnum.ADMINISTRADOR and entrega.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega não encontrada.")
    if current_user.roles_efetivos & set(_REGISTRADORES):
        return entrega
    unidade_ids = {u.id for u in current_user.unidades}
    if entrega.unidade_id not in unidade_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrega não encontrada.")
    return entrega


@router.post("", response_model=EntregaRead, status_code=status.HTTP_201_CREATED)
def registrar_entrega(
    payload: EntregaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_REGISTRADORES)),
) -> Entrega:
    predio_id = resolver_predio_id(current_user, payload.predio_id)

    unidade = db.get(Unidade, payload.unidade_id)
    if unidade is None or unidade.deleted_at is not None or unidade.predio_id != predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    entrega = Entrega(
        predio_id=predio_id,
        unidade_id=payload.unidade_id,
        descricao=payload.descricao,
        localizacao=payload.localizacao,
        created_by=current_user.id,
    )
    db.add(entrega)
    db.flush()

    destinatarios = ids_usuarios_da_unidade(db, payload.unidade_id) - {current_user.id}
    notificar_usuarios(
        db,
        predio_id=predio_id,
        usuario_ids=destinatarios,
        tipo=TipoNotificacaoEnum.ENTREGA,
        titulo="Nova entrega na portaria",
        mensagem=f"{payload.descricao} - {payload.localizacao}",
        referencia_tipo="entrega",
        referencia_id=entrega.id,
    )

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="entregas",
        entidade_id=entrega.id,
        dados_depois=model_to_audit_dict(entrega),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(entrega)
    return entrega


@router.get("", response_model=list[EntregaRead])
def listar_entregas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
    unidade_id: int | None = None,
    apenas_pendentes: bool = False,
) -> list[Entrega]:
    query = db.query(Entrega)

    if current_user.roles_efetivos & set(_REGISTRADORES):
        if current_user.role == RoleEnum.ADMINISTRADOR:
            if predio_id is not None:
                query = query.filter(Entrega.predio_id == predio_id)
        else:
            query = query.filter(Entrega.predio_id == current_user.predio_id)
        if unidade_id is not None:
            query = query.filter(Entrega.unidade_id == unidade_id)
    else:
        unidade_ids = [u.id for u in current_user.unidades]
        if not unidade_ids:
            return []
        query = query.filter(
            Entrega.predio_id == current_user.predio_id, Entrega.unidade_id.in_(unidade_ids)
        )

    if apenas_pendentes:
        query = query.filter(Entrega.retirada_em.is_(None))

    return query.order_by(Entrega.created_at.desc()).all()


@router.post("/{entrega_id}/retirar", response_model=EntregaRead)
def marcar_retirada(
    entrega_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> Entrega:
    entrega = _entrega_ou_404(db, entrega_id, current_user)
    if entrega.retirada_em is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta entrega já foi retirada.")

    entrega.retirada_em = datetime.now(timezone.utc)
    entrega.retirada_por = current_user.id
    db.add(entrega)
    db.commit()
    db.refresh(entrega)
    return entrega
