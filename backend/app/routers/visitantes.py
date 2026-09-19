from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.models.enums import RoleEnum
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.models.visitante import Visitante
from app.schemas.visitante import VisitanteCreate, VisitanteRead

router = APIRouter(prefix="/visitantes", tags=["visitantes"])

# Só quem opera a portaria/gestão vê e registra o livro de visitantes -
# nunca o morador (spec: "podera ser visto pelo zelador e pelo sindico e
# pelo admin").
_PORTARIA = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO, RoleEnum.ZELADOR)


@router.post("", response_model=VisitanteRead, status_code=status.HTTP_201_CREATED)
def registrar_visitante(
    payload: VisitanteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_PORTARIA)),
) -> Visitante:
    predio_id = resolver_predio_id(current_user, payload.predio_id)

    unidade = db.get(Unidade, payload.unidade_id)
    if unidade is None or unidade.deleted_at is not None or unidade.predio_id != predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    visitante = Visitante(
        predio_id=predio_id,
        unidade_id=payload.unidade_id,
        nome_completo=payload.nome_completo,
        tipo_documento=payload.tipo_documento,
        numero_documento=payload.numero_documento,
        created_by=current_user.id,
    )
    db.add(visitante)
    db.commit()
    db.refresh(visitante)
    return visitante


@router.get("", response_model=list[VisitanteRead])
def listar_visitantes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_PORTARIA)),
    predio_id: int | None = None,
    unidade_id: int | None = None,
) -> list[Visitante]:
    query = db.query(Visitante)

    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id is not None:
            query = query.filter(Visitante.predio_id == predio_id)
    else:
        query = query.filter(Visitante.predio_id == current_user.predio_id)

    if unidade_id is not None:
        query = query.filter(Visitante.unidade_id == unidade_id)

    return query.order_by(Visitante.created_at.desc()).all()
