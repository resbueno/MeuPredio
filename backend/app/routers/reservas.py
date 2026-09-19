from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.models.area_comum import AreaComum
from app.models.enums import RoleEnum, StatusReservaEnum
from app.models.reserva import Reserva
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.reserva import ReservaCreate, ReservaRead

router = APIRouter(prefix="/reservas", tags=["reservas"])

_GESTAO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _reserva_ou_404(db: Session, reserva_id: int, current_user: Usuario) -> Reserva:
    reserva = db.get(Reserva, reserva_id)
    if reserva is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")
    if current_user.role != RoleEnum.ADMINISTRADOR and reserva.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")
    if current_user.roles_efetivos & set(_GESTAO):
        return reserva
    unidade_ids = {u.id for u in current_user.unidades}
    if reserva.unidade_id not in unidade_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")
    return reserva


@router.post("", response_model=ReservaRead, status_code=status.HTTP_201_CREATED)
def criar_reserva(
    payload: ReservaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> Reserva:
    predio_id = resolver_predio_id(current_user, payload.predio_id)
    e_gestao = bool(current_user.roles_efetivos & set(_GESTAO))

    if e_gestao:
        if payload.unidade_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Informe a unidade_id para reservar em nome dela.",
            )
        unidade_id = payload.unidade_id
    else:
        minhas_unidades = {u.id for u in current_user.unidades}
        if not minhas_unidades:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não está vinculado a nenhuma unidade.",
            )
        if payload.unidade_id is not None and payload.unidade_id not in minhas_unidades:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você só pode reservar em nome da sua própria unidade.",
            )
        unidade_id = payload.unidade_id or next(iter(minhas_unidades))

    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.deleted_at is not None or unidade.predio_id != predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    area = db.get(AreaComum, payload.area_comum_id)
    if area is None or area.deleted_at is not None or area.predio_id != predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Área não encontrada.")
    if not area.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta área não está disponível para reserva.")

    hoje = date.today()
    if payload.data < hoje:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Não é possível reservar uma data no passado.")
    if area.agenda_liberada_ate is None or payload.data > area.agenda_liberada_ate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta data ainda não está liberada na agenda desta área.",
        )

    # Checagem otimista (evita o caminho de IntegrityError no caso comum) -
    # o índice parcial único (area_comum_id, data) WHERE status='confirmada'
    # continua sendo a garantia real contra corrida de concorrência.
    ja_reservada = (
        db.query(Reserva)
        .filter(
            Reserva.area_comum_id == payload.area_comum_id,
            Reserva.data == payload.data,
            Reserva.status == StatusReservaEnum.CONFIRMADA,
        )
        .first()
    )
    if ja_reservada is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta área já está reservada para esta data.",
        )

    reserva = Reserva(
        predio_id=predio_id,
        area_comum_id=payload.area_comum_id,
        unidade_id=unidade_id,
        data=payload.data,
        observacoes=payload.observacoes,
        created_by=current_user.id,
    )
    db.add(reserva)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta área já está reservada para esta data.",
        ) from None
    db.refresh(reserva)
    return reserva


@router.get("", response_model=list[ReservaRead])
def listar_reservas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
    area_comum_id: int | None = None,
    unidade_id: int | None = None,
) -> list[Reserva]:
    query = db.query(Reserva)

    if current_user.roles_efetivos & set(_GESTAO):
        if current_user.role == RoleEnum.ADMINISTRADOR:
            if predio_id is not None:
                query = query.filter(Reserva.predio_id == predio_id)
        else:
            query = query.filter(Reserva.predio_id == current_user.predio_id)
        if unidade_id is not None:
            query = query.filter(Reserva.unidade_id == unidade_id)
    else:
        unidade_ids = [u.id for u in current_user.unidades]
        if not unidade_ids:
            return []
        query = query.filter(
            Reserva.predio_id == current_user.predio_id, Reserva.unidade_id.in_(unidade_ids)
        )

    if area_comum_id is not None:
        query = query.filter(Reserva.area_comum_id == area_comum_id)

    return query.order_by(Reserva.data.desc()).all()


@router.post("/{reserva_id}/cancelar", response_model=ReservaRead)
def cancelar_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> Reserva:
    reserva = _reserva_ou_404(db, reserva_id, current_user)
    if reserva.status != StatusReservaEnum.CONFIRMADA:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Esta reserva já está cancelada.")

    reserva.status = StatusReservaEnum.CANCELADA
    reserva.cancelada_em = datetime.now(timezone.utc)
    reserva.cancelada_por = current_user.id
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return reserva
