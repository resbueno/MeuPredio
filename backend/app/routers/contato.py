from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.models.contato_lead import ContatoLead
from app.models.enums import RoleEnum
from app.schemas.contato_lead import ContatoLeadCreate, ContatoLeadRead

router = APIRouter(prefix="/contato", tags=["contato"])


@router.post("", response_model=ContatoLeadRead, status_code=status.HTTP_201_CREATED)
def enviar_contato(payload: ContatoLeadCreate, db: Session = Depends(get_db)) -> ContatoLead:
    """Público (sem autenticação) - é o formulário "Começar agora" da
    landing page institucional, para quem ainda não é cliente."""
    lead = ContatoLead(
        nome=payload.nome,
        email=payload.email,
        telefone=payload.telefone,
        mensagem=payload.mensagem,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("", response_model=list[ContatoLeadRead])
def listar_contatos(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(RoleEnum.ADMINISTRADOR)),
    apenas_pendentes: bool = False,
) -> list[ContatoLead]:
    query = db.query(ContatoLead)
    if apenas_pendentes:
        query = query.filter(ContatoLead.atendido.is_(False))
    return query.order_by(ContatoLead.created_at.desc()).all()


@router.post("/{lead_id}/marcar-atendido", response_model=ContatoLeadRead)
def marcar_atendido(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(RoleEnum.ADMINISTRADOR)),
) -> ContatoLead:
    lead = db.get(ContatoLead, lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contato não encontrado.")
    lead.atendido = True
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead
