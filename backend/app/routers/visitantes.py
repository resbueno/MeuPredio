from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.models.enums import RoleEnum
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.models.visitante import Visitante
from app.schemas.visitante import VisitanteCreate, VisitanteItem, VisitanteLoteCreate, VisitanteRead

router = APIRouter(prefix="/visitantes", tags=["visitantes"])

# Só quem opera a portaria/gestão vê e registra o livro de visitantes -
# nunca o morador (spec: "podera ser visto pelo zelador e pelo sindico e
# pelo admin").
_PORTARIA = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO, RoleEnum.ZELADOR)


def _montar_visitante(
    item: VisitanteItem, *, predio_id: int, unidade_id: int, created_by: int
) -> Visitante:
    return Visitante(
        predio_id=predio_id,
        unidade_id=unidade_id,
        nome_completo=item.nome_completo,
        tipo_documento=item.tipo_documento,
        numero_documento=item.numero_documento,
        veiculo_placa=item.veiculo_placa,
        veiculo_modelo=item.veiculo_modelo,
        veiculo_cor=item.veiculo_cor,
        created_by=created_by,
    )


def _validar_unidade(db: Session, unidade_id: int, predio_id: int) -> None:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.deleted_at is not None or unidade.predio_id != predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")


@router.post("", response_model=VisitanteRead, status_code=status.HTTP_201_CREATED)
def registrar_visitante(
    payload: VisitanteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_PORTARIA)),
) -> Visitante:
    predio_id = resolver_predio_id(current_user, payload.predio_id)
    _validar_unidade(db, payload.unidade_id, predio_id)

    visitante = _montar_visitante(
        payload, predio_id=predio_id, unidade_id=payload.unidade_id, created_by=current_user.id
    )
    db.add(visitante)
    db.commit()
    db.refresh(visitante)
    return visitante


@router.post("/lote", response_model=list[VisitanteRead], status_code=status.HTTP_201_CREATED)
def registrar_visitantes_em_lote(
    payload: VisitanteLoteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_PORTARIA)),
) -> list[Visitante]:
    """Registra vários visitantes da mesma unidade em uma única chamada
    (ex.: convidados de um evento) - tudo ou nada: se um item for
    inválido, nenhum é gravado."""
    predio_id = resolver_predio_id(current_user, payload.predio_id)
    _validar_unidade(db, payload.unidade_id, predio_id)

    visitantes = [
        _montar_visitante(
            item, predio_id=predio_id, unidade_id=payload.unidade_id, created_by=current_user.id
        )
        for item in payload.visitantes
    ]
    db.add_all(visitantes)
    db.commit()
    for visitante in visitantes:
        db.refresh(visitante)
    return visitantes


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
