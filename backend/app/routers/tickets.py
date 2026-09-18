from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.core.tickets import calcular_prazo_sla
from app.models.enums import RoleEnum, StatusTicketEnum
from app.models.ticket_atendimento import TicketAtendimento
from app.models.ticket_comentario import TicketComentario
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.ticket_atendimento import (
    TicketAtendimentoAssumir,
    TicketAtendimentoAtualizar,
    TicketAtendimentoCreate,
    TicketAtendimentoRead,
    TicketComentarioCreate,
    TicketComentarioRead,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])

# Quem gerencia o fluxo de QUALQUER chamado do predio (assumir/resolver,
# ver todos). Morador/proprietario so enxergam e agem sobre os proprios
# chamados (ver `_pode_ver`) - igual a como despesas.py restringe a
# _FINANCEIRO, mas aqui o recurso e criado por qualquer papel, so a GESTAO
# dele e restrita.
_GESTAO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO, RoleEnum.ZELADOR)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _ticket_ou_404(db: Session, ticket_id: int, current_user: Usuario) -> TicketAtendimento:
    ticket = db.get(TicketAtendimento, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chamado nao encontrado.")
    if current_user.role != RoleEnum.ADMINISTRADOR and ticket.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chamado nao encontrado.")
    return ticket


def _exigir_pode_ver(ticket: TicketAtendimento, current_user: Usuario) -> None:
    """Alem do isolamento por predio (`_ticket_ou_404`), um morador so pode
    ver/comentar/cancelar o PROPRIO chamado - a gestao (sindico/zelador/
    administrador) ve todos os do predio."""
    e_gestao = current_user.role in _GESTAO
    if not e_gestao and ticket.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chamado nao encontrado.")


def _exigir_status(ticket: TicketAtendimento, permitidos: tuple[StatusTicketEnum, ...], acao: str) -> None:
    if ticket.status not in permitidos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Nao e possivel {acao} um chamado com status atual '{ticket.status.value}'.",
        )


def _validar_unidade(db: Session, unidade_id: int | None, predio_id: int) -> None:
    if unidade_id is None:
        return
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.deleted_at is not None or unidade.predio_id != predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade nao encontrada.")


@router.post("", response_model=TicketAtendimentoRead, status_code=status.HTTP_201_CREATED)
def criar_ticket(
    payload: TicketAtendimentoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> TicketAtendimento:
    predio_id = resolver_predio_id(current_user, payload.predio_id)
    _validar_unidade(db, payload.unidade_id, predio_id)

    agora = datetime.now(timezone.utc)
    ticket = TicketAtendimento(
        predio_id=predio_id,
        unidade_id=payload.unidade_id,
        titulo=payload.titulo,
        descricao=payload.descricao,
        categoria=payload.categoria,
        prioridade=payload.prioridade,
        status=StatusTicketEnum.ABERTO,
        prazo_sla=calcular_prazo_sla(payload.prioridade, agora),
        created_by=current_user.id,
    )
    db.add(ticket)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="tickets_atendimento",
        entidade_id=ticket.id,
        dados_depois=model_to_audit_dict(ticket),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=list[TicketAtendimentoRead])
def listar_tickets(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
    status_: StatusTicketEnum | None = None,
) -> list[TicketAtendimento]:
    query = db.query(TicketAtendimento)

    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id is not None:
            query = query.filter(TicketAtendimento.predio_id == predio_id)
    else:
        query = query.filter(TicketAtendimento.predio_id == current_user.predio_id)
        if current_user.role not in _GESTAO:
            query = query.filter(TicketAtendimento.created_by == current_user.id)

    if status_ is not None:
        query = query.filter(TicketAtendimento.status == status_)

    return query.order_by(TicketAtendimento.created_at.desc()).all()


@router.get("/{ticket_id}", response_model=TicketAtendimentoRead)
def obter_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> TicketAtendimento:
    ticket = _ticket_ou_404(db, ticket_id, current_user)
    _exigir_pode_ver(ticket, current_user)
    return ticket


@router.patch("/{ticket_id}", response_model=TicketAtendimentoRead)
def atualizar_ticket(
    ticket_id: int,
    payload: TicketAtendimentoAtualizar,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> TicketAtendimento:
    ticket = _ticket_ou_404(db, ticket_id, current_user)
    if ticket.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="So quem abriu o chamado pode edita-lo.",
        )
    _exigir_status(ticket, (StatusTicketEnum.ABERTO,), "editar")

    campos_enviados = payload.model_dump(exclude_unset=True)
    dados_antes = model_to_audit_dict(ticket)

    for campo in ("titulo", "descricao", "categoria", "prioridade"):
        if campo in campos_enviados:
            setattr(ticket, campo, campos_enviados[campo])
    if "prioridade" in campos_enviados:
        ticket.prazo_sla = calcular_prazo_sla(ticket.prioridade, ticket.created_at)

    db.add(ticket)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="tickets_atendimento",
        entidade_id=ticket.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(ticket),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/assumir", response_model=TicketAtendimentoRead)
def assumir_ticket(
    ticket_id: int,
    payload: TicketAtendimentoAssumir,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> TicketAtendimento:
    ticket = _ticket_ou_404(db, ticket_id, current_user)
    _exigir_status(ticket, (StatusTicketEnum.ABERTO,), "assumir")

    responsavel_id = payload.responsavel_id or current_user.id
    if payload.responsavel_id is not None:
        responsavel = db.get(Usuario, responsavel_id)
        if (
            responsavel is None
            or responsavel.is_deleted
            or responsavel.role not in _GESTAO
            or responsavel.predio_id != ticket.predio_id
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Responsavel nao encontrado."
            )

    dados_antes = model_to_audit_dict(ticket)
    ticket.status = StatusTicketEnum.EM_ANDAMENTO
    ticket.responsavel_id = responsavel_id
    db.add(ticket)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="tickets_atendimento",
        entidade_id=ticket.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(ticket),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/resolver", response_model=TicketAtendimentoRead)
def resolver_ticket(
    ticket_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> TicketAtendimento:
    ticket = _ticket_ou_404(db, ticket_id, current_user)
    _exigir_status(ticket, (StatusTicketEnum.ABERTO, StatusTicketEnum.EM_ANDAMENTO), "resolver")

    dados_antes = model_to_audit_dict(ticket)
    ticket.status = StatusTicketEnum.RESOLVIDO
    ticket.resolvido_em = datetime.now(timezone.utc)
    db.add(ticket)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="tickets_atendimento",
        entidade_id=ticket.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(ticket),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/cancelar", response_model=TicketAtendimentoRead)
def cancelar_ticket(
    ticket_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> TicketAtendimento:
    ticket = _ticket_ou_404(db, ticket_id, current_user)
    _exigir_pode_ver(ticket, current_user)
    _exigir_status(ticket, (StatusTicketEnum.ABERTO, StatusTicketEnum.EM_ANDAMENTO), "cancelar")

    dados_antes = model_to_audit_dict(ticket)
    ticket.status = StatusTicketEnum.CANCELADO
    db.add(ticket)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="tickets_atendimento",
        entidade_id=ticket.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(ticket),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post(
    "/{ticket_id}/comentarios",
    response_model=TicketComentarioRead,
    status_code=status.HTTP_201_CREATED,
)
def comentar_ticket(
    ticket_id: int,
    payload: TicketComentarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> TicketComentario:
    ticket = _ticket_ou_404(db, ticket_id, current_user)
    _exigir_pode_ver(ticket, current_user)

    comentario = TicketComentario(
        predio_id=ticket.predio_id,
        ticket_id=ticket.id,
        mensagem=payload.mensagem,
        created_by=current_user.id,
    )
    db.add(comentario)
    db.commit()
    db.refresh(comentario)
    return comentario
