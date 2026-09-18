from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.models.despesa_lancamento import DespesaLancamento
from app.models.enums import RoleEnum, StatusDespesaEnum
from app.models.usuario import Usuario
from app.schemas.transparencia import BalanceteResponse, DespesaTransparenciaRead, TotalPorCategoria

router = APIRouter(prefix="/transparencia", tags=["transparencia"])

# Portal da Transparencia (roadmap Fase 3): leitura para QUALQUER papel
# autenticado do predio (morador/proprietario/zelador incluidos, nao so
# ADMINISTRADOR/SINDICO como em despesas.py - "prestacao de contas em tempo
# real" so faz sentido se o condomino de verdade conseguir ver).
# require_role() sem argumentos == qualquer usuario autenticado.


def _predio_id_efetivo(current_user: Usuario, predio_id_informado: int | None) -> int:
    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id_informado is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Administrador precisa informar predio_id explicitamente.",
            )
        return predio_id_informado
    return current_user.predio_id  # type: ignore[return-value]


_GESTAO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO, RoleEnum.ZELADOR)


def _restringir_por_unidade(query, current_user: Usuario):
    """Uma despesa com `unidade_id` preenchido (multa/cobrança exclusiva,
    ver DespesaLancamento.unidade_id) só é visível à gestão e a quem mora/é
    dono daquela unidade - nunca aos demais condôminos. Despesas gerais
    (`unidade_id is None`) continuam públicas a todo mundo do prédio."""
    if current_user.role in _GESTAO:
        return query
    unidade_ids = [u.id for u in current_user.unidades]
    return query.filter(
        or_(DespesaLancamento.unidade_id.is_(None), DespesaLancamento.unidade_id.in_(unidade_ids))
    )


def _limites_periodo(ano: int, mes: int | None) -> tuple[date, date]:
    """`mes=None` (ou 0) significa "ano inteiro" - `mes` entre 1 e 12 filtra
    para aquele mes especifico."""
    if mes:
        inicio = date(ano, mes, 1)
        fim_exclusivo = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    else:
        inicio = date(ano, 1, 1)
        fim_exclusivo = date(ano + 1, 1, 1)
    return inicio, fim_exclusivo


@router.get("/despesas", response_model=list[DespesaTransparenciaRead])
def listar_despesas_transparencia(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
    ano: int | None = None,
    mes: int | None = None,
) -> list[DespesaLancamento]:
    predio_id_efetivo = _predio_id_efetivo(current_user, predio_id)

    query = db.query(DespesaLancamento).filter(
        DespesaLancamento.predio_id == predio_id_efetivo,
        DespesaLancamento.deleted_at.is_(None),
    )
    query = _restringir_por_unidade(query, current_user)
    if ano is not None:
        inicio, fim_exclusivo = _limites_periodo(ano, mes)
        query = query.filter(
            DespesaLancamento.data_vencimento >= inicio,
            DespesaLancamento.data_vencimento < fim_exclusivo,
        )

    return query.order_by(DespesaLancamento.data_vencimento.desc()).all()


@router.get("/balancete", response_model=BalanceteResponse)
def obter_balancete(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
    ano: int | None = Query(default=None),
    mes: int | None = Query(default=None, ge=0, le=12),
) -> BalanceteResponse:
    predio_id_efetivo = _predio_id_efetivo(current_user, predio_id)
    hoje = date.today()
    ano_efetivo = ano if ano is not None else hoje.year
    mes_efetivo = mes if mes is not None else hoje.month
    inicio, fim_exclusivo = _limites_periodo(ano_efetivo, mes_efetivo)

    base = db.query(DespesaLancamento).filter(
        DespesaLancamento.predio_id == predio_id_efetivo,
        DespesaLancamento.deleted_at.is_(None),
        DespesaLancamento.data_vencimento >= inicio,
        DespesaLancamento.data_vencimento < fim_exclusivo,
    )
    base = _restringir_por_unidade(base, current_user)

    totais_por_status = dict(
        base.with_entities(DespesaLancamento.status, func.sum(DespesaLancamento.valor))
        .group_by(DespesaLancamento.status)
        .all()
    )
    total_pago = totais_por_status.get(StatusDespesaEnum.PAGO, Decimal("0"))
    total_pendente = totais_por_status.get(StatusDespesaEnum.PENDENTE, Decimal("0"))
    total_cancelado = totais_por_status.get(StatusDespesaEnum.CANCELADO, Decimal("0"))

    por_categoria = [
        TotalPorCategoria(categoria=categoria, total=total)
        for categoria, total in (
            base.filter(DespesaLancamento.status != StatusDespesaEnum.CANCELADO)
            .with_entities(DespesaLancamento.categoria, func.sum(DespesaLancamento.valor))
            .group_by(DespesaLancamento.categoria)
            .order_by(DespesaLancamento.categoria)
            .all()
        )
    ]

    return BalanceteResponse(
        ano=ano_efetivo,
        mes=mes_efetivo or None,
        total_pago=total_pago,
        total_pendente=total_pendente,
        total_cancelado=total_cancelado,
        total_geral=total_pago + total_pendente,
        por_categoria=por_categoria,
    )
