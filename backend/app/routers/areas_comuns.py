from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.models.area_comum import AreaComum
from app.models.enums import RoleEnum
from app.models.usuario import Usuario
from app.schemas.area_comum import (
    AreaComumAtualizar,
    AreaComumCreate,
    AreaComumLiberarAgenda,
    AreaComumRead,
)

router = APIRouter(prefix="/areas-comuns", tags=["areas-comuns"])

# Só síndico/administrador cadastra área e gerencia a agenda - o morador só
# consome (ver routers/reservas.py).
_GESTAO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _area_ou_404(db: Session, area_id: int, current_user: Usuario) -> AreaComum:
    area = db.get(AreaComum, area_id)
    if area is None or area.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Área não encontrada.")
    if current_user.role != RoleEnum.ADMINISTRADOR and area.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Área não encontrada.")
    return area


@router.post("", response_model=AreaComumRead, status_code=status.HTTP_201_CREATED)
def criar_area_comum(
    payload: AreaComumCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> AreaComum:
    predio_id = resolver_predio_id(current_user, payload.predio_id)

    area = AreaComum(
        predio_id=predio_id,
        nome=payload.nome,
        descricao=payload.descricao,
        capacidade=payload.capacidade,
        created_by=current_user.id,
    )
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


@router.get("", response_model=list[AreaComumRead])
def listar_areas_comuns(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
    apenas_ativas: bool = False,
) -> list[AreaComum]:
    query = db.query(AreaComum).filter(AreaComum.deleted_at.is_(None))

    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id is not None:
            query = query.filter(AreaComum.predio_id == predio_id)
    else:
        query = query.filter(AreaComum.predio_id == current_user.predio_id)

    if apenas_ativas:
        query = query.filter(AreaComum.ativo.is_(True))

    return query.order_by(AreaComum.nome.asc()).all()


@router.patch("/{area_id}", response_model=AreaComumRead)
def atualizar_area_comum(
    area_id: int,
    payload: AreaComumAtualizar,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> AreaComum:
    area = _area_ou_404(db, area_id, current_user)

    campos_enviados = payload.model_dump(exclude_unset=True)
    for campo in ("nome", "descricao", "capacidade", "ativo"):
        if campo in campos_enviados:
            setattr(area, campo, campos_enviados[campo])
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


@router.post("/{area_id}/liberar-agenda", response_model=AreaComumRead)
def liberar_agenda(
    area_id: int,
    payload: AreaComumLiberarAgenda,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> AreaComum:
    area = _area_ou_404(db, area_id, current_user)

    nova_data = payload.ate if payload.ate is not None else date.today() + timedelta(days=payload.dias)  # type: ignore[arg-type]
    if nova_data < date.today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="A data de liberação não pode ser no passado.",
        )

    area.agenda_liberada_ate = nova_data
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


@router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_area_comum(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> None:
    area = _area_ou_404(db, area_id, current_user)
    area.deleted_at = datetime.now(timezone.utc)
    db.add(area)
    db.commit()
    return None
