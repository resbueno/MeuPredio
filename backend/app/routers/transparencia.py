from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_role
from app.models.despesa_lancamento import DespesaLancamento
from app.models.enums import RoleEnum, StatusDespesaEnum
from app.models.rateio_despesa_item import RateioDespesaItem
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.transparencia import (
    BalanceteMensal,
    BalanceteResponse,
    DespesaTransparenciaRead,
    PreviaUnidadeItem,
    PreviaUnidadeResponse,
    TotalPorCategoria,
)

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
    if current_user.roles_efetivos & set(_GESTAO):
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


def _mes_anterior(ano: int, mes: int) -> tuple[int, int]:
    return (ano - 1, 12) if mes == 1 else (ano, mes - 1)


def _totais_por_status(
    db: Session, predio_id: int, current_user: Usuario, inicio: date, fim_exclusivo: date
) -> dict[StatusDespesaEnum, Decimal]:
    base = db.query(DespesaLancamento).filter(
        DespesaLancamento.predio_id == predio_id,
        DespesaLancamento.deleted_at.is_(None),
        DespesaLancamento.data_vencimento >= inicio,
        DespesaLancamento.data_vencimento < fim_exclusivo,
    )
    base = _restringir_por_unidade(base, current_user)
    return dict(
        base.with_entities(DespesaLancamento.status, func.sum(DespesaLancamento.valor))
        .group_by(DespesaLancamento.status)
        .all()
    )


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

    totais_por_status = _totais_por_status(db, predio_id_efetivo, current_user, inicio, fim_exclusivo)
    total_pago = totais_por_status.get(StatusDespesaEnum.PAGO, Decimal("0"))
    total_pendente = totais_por_status.get(StatusDespesaEnum.PENDENTE, Decimal("0"))
    total_cancelado = totais_por_status.get(StatusDespesaEnum.CANCELADO, Decimal("0"))

    base_categoria = db.query(DespesaLancamento).filter(
        DespesaLancamento.predio_id == predio_id_efetivo,
        DespesaLancamento.deleted_at.is_(None),
        DespesaLancamento.data_vencimento >= inicio,
        DespesaLancamento.data_vencimento < fim_exclusivo,
        DespesaLancamento.status != StatusDespesaEnum.CANCELADO,
    )
    base_categoria = _restringir_por_unidade(base_categoria, current_user)
    por_categoria = [
        TotalPorCategoria(categoria=categoria, total=total)
        for categoria, total in (
            base_categoria.with_entities(DespesaLancamento.categoria, func.sum(DespesaLancamento.valor))
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


@router.get("/balancete/serie", response_model=list[BalanceteMensal])
def obter_serie_mensal(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
    meses: int = Query(default=6, ge=1, le=24),
) -> list[BalanceteMensal]:
    """Serie dos ultimos `meses` meses (mais antigo primeiro) - usada pelo
    grafico de tendencia do Portal da Transparencia."""
    predio_id_efetivo = _predio_id_efetivo(current_user, predio_id)
    hoje = date.today()

    pontos: list[BalanceteMensal] = []
    ano_atual, mes_atual = hoje.year, hoje.month
    for _ in range(meses):
        inicio, fim_exclusivo = _limites_periodo(ano_atual, mes_atual)
        totais = _totais_por_status(db, predio_id_efetivo, current_user, inicio, fim_exclusivo)
        total_pago = totais.get(StatusDespesaEnum.PAGO, Decimal("0"))
        total_pendente = totais.get(StatusDespesaEnum.PENDENTE, Decimal("0"))
        pontos.append(
            BalanceteMensal(
                ano=ano_atual,
                mes=mes_atual,
                total_pago=total_pago,
                total_pendente=total_pendente,
                total_geral=total_pago + total_pendente,
            )
        )
        ano_atual, mes_atual = _mes_anterior(ano_atual, mes_atual)

    return list(reversed(pontos))


@router.get("/previa-unidade", response_model=PreviaUnidadeResponse)
def obter_previa_unidade(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    unidade_id: int | None = None,
    ano: int | None = Query(default=None),
    mes: int | None = Query(default=None, ge=1, le=12),
) -> PreviaUnidadeResponse:
    """Previa da conta de condominio de UMA unidade: a fatia dela nas
    despesas gerais ratejadas naquele periodo + qualquer despesa exclusiva
    sua (multa, ver DespesaLancamento.unidade_id) - a soma que a unidade
    efetivamente deve pagar naquele mes."""
    e_gestao = bool(current_user.roles_efetivos & set(_GESTAO))
    if unidade_id is None:
        if e_gestao:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Informe unidade_id.",
            )
        minhas_unidades = current_user.unidades
        if not minhas_unidades:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Você não está vinculado a nenhuma unidade."
            )
        unidade_id = minhas_unidades[0].id

    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")
    if current_user.role != RoleEnum.ADMINISTRADOR and unidade.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")
    if not e_gestao and unidade_id not in {u.id for u in current_user.unidades}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode ver a prévia das próprias unidades.",
        )

    hoje = date.today()
    ano_efetivo = ano if ano is not None else hoje.year
    mes_efetivo = mes if mes is not None else hoje.month
    inicio, fim_exclusivo = _limites_periodo(ano_efetivo, mes_efetivo)

    itens_rateio = (
        db.query(RateioDespesaItem, DespesaLancamento)
        .join(DespesaLancamento, RateioDespesaItem.despesa_lancamento_id == DespesaLancamento.id)
        .filter(
            RateioDespesaItem.unidade_id == unidade_id,
            DespesaLancamento.deleted_at.is_(None),
            DespesaLancamento.status != StatusDespesaEnum.CANCELADO,
            DespesaLancamento.data_vencimento >= inicio,
            DespesaLancamento.data_vencimento < fim_exclusivo,
        )
        .all()
    )
    despesas_exclusivas = (
        db.query(DespesaLancamento)
        .filter(
            DespesaLancamento.unidade_id == unidade_id,
            DespesaLancamento.deleted_at.is_(None),
            DespesaLancamento.status != StatusDespesaEnum.CANCELADO,
            DespesaLancamento.data_vencimento >= inicio,
            DespesaLancamento.data_vencimento < fim_exclusivo,
        )
        .all()
    )

    itens = [
        PreviaUnidadeItem(
            despesa_id=despesa.id,
            descricao=despesa.descricao,
            categoria=despesa.categoria,
            tipo="rateio",
            valor=item.valor,
            status=despesa.status,
            data_vencimento=despesa.data_vencimento,
        )
        for item, despesa in itens_rateio
    ] + [
        PreviaUnidadeItem(
            despesa_id=despesa.id,
            descricao=despesa.descricao,
            categoria=despesa.categoria,
            tipo="multa",
            valor=despesa.valor,
            status=despesa.status,
            data_vencimento=despesa.data_vencimento,
        )
        for despesa in despesas_exclusivas
    ]

    total_rateio = sum((item.valor for item, _ in itens_rateio), Decimal("0"))
    total_multas = sum((despesa.valor for despesa in despesas_exclusivas), Decimal("0"))

    return PreviaUnidadeResponse(
        unidade_id=unidade_id,
        ano=ano_efetivo,
        mes=mes_efetivo,
        total_rateio=total_rateio,
        total_multas=total_multas,
        total_geral=total_rateio + total_multas,
        itens=sorted(itens, key=lambda i: i.data_vencimento),
    )
