from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_db, require_role
from app.models.despesa_lancamento import DespesaLancamento
from app.models.enums import RoleEnum, StatusDespesaEnum
from app.models.fornecedor import Fornecedor
from app.models.usuario import Usuario
from app.schemas.despesa_lancamento import (
    DespesaLancamentoCreate,
    DespesaLancamentoRead,
    DespesaLancamentoRegistrarPagamento,
    DespesaLancamentoUpdate,
)

router = APIRouter(prefix="/despesas", tags=["despesas"])

# Mesmo escopo de acesso de fornecedores.py: motor financeiro restrito a
# síndico/administrador nesta fatia da Fase 2 (ver comentário lá).
_FINANCEIRO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _despesa_ou_404(db: Session, despesa_id: int) -> DespesaLancamento:
    despesa = db.get(DespesaLancamento, despesa_id)
    if despesa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa nao encontrada.")
    return despesa


def _validar_fornecedor(db: Session, fornecedor_id: int | None) -> None:
    if fornecedor_id is None:
        return
    fornecedor = db.get(Fornecedor, fornecedor_id)
    if fornecedor is None or fornecedor.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor nao encontrado.")


def _exigir_pendente(despesa: DespesaLancamento, acao: str) -> None:
    if despesa.status != StatusDespesaEnum.PENDENTE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"So e possivel {acao} um lancamento pendente (status atual: {despesa.status.value}).",
        )


@router.post("", response_model=DespesaLancamentoRead, status_code=status.HTTP_201_CREATED)
def criar_despesa(
    payload: DespesaLancamentoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    _validar_fornecedor(db, payload.fornecedor_id)

    despesa = DespesaLancamento(
        fornecedor_id=payload.fornecedor_id,
        descricao=payload.descricao,
        categoria=payload.categoria,
        valor=payload.valor,
        data_vencimento=payload.data_vencimento,
        observacoes=payload.observacoes,
        status=StatusDespesaEnum.PENDENTE,
        created_by=current_user.id,
    )
    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa


@router.get("", response_model=list[DespesaLancamentoRead])
def listar_despesas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
    status_: StatusDespesaEnum | None = Query(default=None, alias="status"),
    categoria: str | None = None,
    fornecedor_id: int | None = None,
    incluir_inativos: bool = False,
) -> list[DespesaLancamento]:
    query = db.query(DespesaLancamento)
    if not incluir_inativos:
        query = query.filter(DespesaLancamento.deleted_at.is_(None))
    if status_ is not None:
        query = query.filter(DespesaLancamento.status == status_)
    if categoria is not None:
        query = query.filter(DespesaLancamento.categoria == categoria)
    if fornecedor_id is not None:
        query = query.filter(DespesaLancamento.fornecedor_id == fornecedor_id)
    return query.order_by(DespesaLancamento.data_vencimento).all()


@router.get("/{despesa_id}", response_model=DespesaLancamentoRead)
def obter_despesa(
    despesa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    return _despesa_ou_404(db, despesa_id)


@router.patch("/{despesa_id}", response_model=DespesaLancamentoRead)
def atualizar_despesa(
    despesa_id: int,
    payload: DespesaLancamentoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    despesa = _despesa_ou_404(db, despesa_id)
    _exigir_pendente(despesa, "editar")
    campos_enviados = payload.model_dump(exclude_unset=True)

    if "fornecedor_id" in campos_enviados:
        _validar_fornecedor(db, campos_enviados["fornecedor_id"])

    dados_antes = model_to_audit_dict(despesa)

    for campo in ("fornecedor_id", "descricao", "categoria", "valor", "data_vencimento", "observacoes"):
        if campo in campos_enviados:
            setattr(despesa, campo, campos_enviados[campo])

    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa


@router.post("/{despesa_id}/pagar", response_model=DespesaLancamentoRead)
def registrar_pagamento(
    despesa_id: int,
    payload: DespesaLancamentoRegistrarPagamento,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    despesa = _despesa_ou_404(db, despesa_id)
    _exigir_pendente(despesa, "dar baixa em")

    dados_antes = model_to_audit_dict(despesa)
    despesa.status = StatusDespesaEnum.PAGO
    despesa.data_pagamento = payload.data_pagamento
    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa


@router.post("/{despesa_id}/cancelar", response_model=DespesaLancamentoRead)
def cancelar_despesa(
    despesa_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    despesa = _despesa_ou_404(db, despesa_id)
    _exigir_pendente(despesa, "cancelar")

    dados_antes = model_to_audit_dict(despesa)
    despesa.status = StatusDespesaEnum.CANCELADO
    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa


@router.delete("/{despesa_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_despesa(
    despesa_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> None:
    despesa = _despesa_ou_404(db, despesa_id)
    if despesa.deleted_at is not None:
        return None

    dados_antes = model_to_audit_dict(despesa)
    despesa.deleted_at = datetime.now(timezone.utc)
    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="SOFT_DELETE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None
