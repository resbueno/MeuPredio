from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.models.notificacao import Notificacao
from app.models.usuario import Usuario
from app.schemas.notificacao import NotificacaoContagem, NotificacaoRead

router = APIRouter(prefix="/notificacoes", tags=["notificacoes"])


@router.get("", response_model=list[NotificacaoRead])
def listar_notificacoes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    apenas_nao_lidas: bool = False,
    limit: int = 50,
) -> list[Notificacao]:
    query = db.query(Notificacao).filter(Notificacao.usuario_id == current_user.id)
    if apenas_nao_lidas:
        query = query.filter(Notificacao.lida_em.is_(None))
    return query.order_by(Notificacao.created_at.desc()).limit(min(limit, 200)).all()


@router.get("/contagem-nao-lidas", response_model=NotificacaoContagem)
def contar_nao_lidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> NotificacaoContagem:
    total = (
        db.query(Notificacao)
        .filter(Notificacao.usuario_id == current_user.id, Notificacao.lida_em.is_(None))
        .count()
    )
    return NotificacaoContagem(nao_lidas=total)


@router.post("/{notificacao_id}/marcar-lida", response_model=NotificacaoRead)
def marcar_lida(
    notificacao_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> Notificacao:
    notificacao = db.get(Notificacao, notificacao_id)
    if notificacao is None or notificacao.usuario_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificação não encontrada.")
    if notificacao.lida_em is None:
        notificacao.lida_em = datetime.now(timezone.utc)
        db.add(notificacao)
        db.commit()
        db.refresh(notificacao)
    return notificacao


@router.post("/marcar-todas-lidas", status_code=status.HTTP_204_NO_CONTENT)
def marcar_todas_lidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> None:
    agora = datetime.now(timezone.utc)
    db.query(Notificacao).filter(
        Notificacao.usuario_id == current_user.id, Notificacao.lida_em.is_(None)
    ).update({"lida_em": agora})
    db.commit()
    return None
