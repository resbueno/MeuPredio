from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.despesas_recorrentes import gerar_pendentes_do_predio
from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.models.despesa_lancamento import DespesaLancamento
from app.models.despesa_recorrente import DespesaRecorrente
from app.models.enums import RoleEnum
from app.models.fornecedor import Fornecedor
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.despesa_lancamento import DespesaLancamentoRead
from app.schemas.despesa_recorrente import (
    DespesaRecorrenteAtualizar,
    DespesaRecorrenteCreate,
    DespesaRecorrenteRead,
)

router = APIRouter(prefix="/despesas-recorrentes", tags=["despesas-recorrentes"])

_FINANCEIRO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _recorrente_ou_404(db: Session, recorrente_id: int, current_user: Usuario) -> DespesaRecorrente:
    recorrente = db.get(DespesaRecorrente, recorrente_id)
    if recorrente is None or recorrente.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta recorrente não encontrada.")
    if current_user.role != RoleEnum.ADMINISTRADOR and recorrente.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta recorrente não encontrada.")
    return recorrente


@router.post("", response_model=DespesaRecorrenteRead, status_code=status.HTTP_201_CREATED)
def criar_despesa_recorrente(
    payload: DespesaRecorrenteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaRecorrente:
    predio_id = resolver_predio_id(current_user, payload.predio_id)

    if payload.fornecedor_id is not None:
        fornecedor = db.get(Fornecedor, payload.fornecedor_id)
        if fornecedor is None or fornecedor.deleted_at is not None or fornecedor.predio_id != predio_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado.")

    if payload.unidade_id is not None:
        unidade = db.get(Unidade, payload.unidade_id)
        if unidade is None or unidade.deleted_at is not None or unidade.predio_id != predio_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    recorrente = DespesaRecorrente(
        predio_id=predio_id,
        fornecedor_id=payload.fornecedor_id,
        unidade_id=payload.unidade_id,
        descricao=payload.descricao,
        categoria=payload.categoria,
        valor=payload.valor,
        dia_vencimento=payload.dia_vencimento,
        data_inicio=payload.data_inicio,
        data_fim=payload.data_fim,
        observacoes=payload.observacoes,
        created_by=current_user.id,
    )
    db.add(recorrente)
    db.commit()
    db.refresh(recorrente)
    return recorrente


@router.get("", response_model=list[DespesaRecorrenteRead])
def listar_despesas_recorrentes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
    predio_id: int | None = None,
    incluir_inativas: bool = False,
) -> list[DespesaRecorrente]:
    query = db.query(DespesaRecorrente).filter(DespesaRecorrente.deleted_at.is_(None))

    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id is not None:
            query = query.filter(DespesaRecorrente.predio_id == predio_id)
    else:
        query = query.filter(DespesaRecorrente.predio_id == current_user.predio_id)

    if not incluir_inativas:
        query = query.filter(DespesaRecorrente.ativo.is_(True))

    return query.order_by(DespesaRecorrente.descricao.asc()).all()


@router.patch("/{recorrente_id}", response_model=DespesaRecorrenteRead)
def atualizar_despesa_recorrente(
    recorrente_id: int,
    payload: DespesaRecorrenteAtualizar,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaRecorrente:
    recorrente = _recorrente_ou_404(db, recorrente_id, current_user)

    campos_enviados = payload.model_dump(exclude_unset=True)

    if "fornecedor_id" in campos_enviados and campos_enviados["fornecedor_id"] is not None:
        fornecedor = db.get(Fornecedor, campos_enviados["fornecedor_id"])
        if fornecedor is None or fornecedor.deleted_at is not None or fornecedor.predio_id != recorrente.predio_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor não encontrado.")

    if "unidade_id" in campos_enviados and campos_enviados["unidade_id"] is not None:
        unidade = db.get(Unidade, campos_enviados["unidade_id"])
        if unidade is None or unidade.deleted_at is not None or unidade.predio_id != recorrente.predio_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    for campo in (
        "fornecedor_id",
        "unidade_id",
        "descricao",
        "categoria",
        "valor",
        "dia_vencimento",
        "ativo",
        "data_fim",
        "observacoes",
    ):
        if campo in campos_enviados:
            setattr(recorrente, campo, campos_enviados[campo])

    db.add(recorrente)
    db.commit()
    db.refresh(recorrente)
    return recorrente


@router.delete("/{recorrente_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_despesa_recorrente(
    recorrente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> None:
    recorrente = _recorrente_ou_404(db, recorrente_id, current_user)
    recorrente.deleted_at = datetime.now(timezone.utc)
    db.add(recorrente)
    db.commit()
    return None


@router.post("/gerar-pendentes", response_model=list[DespesaLancamentoRead])
def gerar_pendentes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
    predio_id: int | None = None,
) -> list[DespesaLancamento]:
    """Gera os lançamentos de todas as contas recorrentes ativas do prédio
    cujas competências já venceram e ainda não foram lançadas - idempotente,
    seguro para chamar sempre que a tela de Despesas é aberta."""
    predio_resolvido = resolver_predio_id(current_user, predio_id)
    gerados = gerar_pendentes_do_predio(db, predio_resolvido)
    db.commit()
    for lancamento in gerados:
        db.refresh(lancamento)
    return gerados
