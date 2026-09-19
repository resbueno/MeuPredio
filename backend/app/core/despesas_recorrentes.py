"""Geração de lançamentos a partir de uma `DespesaRecorrente` (ver
routers/despesas_recorrentes.py). Só gera até hoje (nunca lançamentos
futuros) e nunca pula/duplica um mês: sempre avança a partir de
`ultima_geracao`, não de "hoje", então rodar isso várias vezes seguidas ou
depois de um tempo parado produz sempre o mesmo resultado final."""
from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.despesa_lancamento import DespesaLancamento
from app.models.despesa_recorrente import DespesaRecorrente
from app.models.enums import StatusDespesaEnum

_MAX_COMPETENCIAS_POR_CHAMADA = 24


def _proximo_mes(referencia: date, dia_vencimento: int) -> date:
    ano, mes = referencia.year, referencia.month + 1
    if mes > 12:
        mes = 1
        ano += 1
    return date(ano, mes, dia_vencimento)


def _primeira_data(data_inicio: date, dia_vencimento: int) -> date:
    candidata = date(data_inicio.year, data_inicio.month, dia_vencimento)
    if candidata < data_inicio:
        candidata = _proximo_mes(candidata, dia_vencimento)
    return candidata


def gerar_pendentes(db: Session, recorrente: DespesaRecorrente) -> list[DespesaLancamento]:
    """Cria um `DespesaLancamento` para cada competência vencida (entre a
    última gerada e hoje) ainda não gerada. Não comita - quem chama decide
    quando persistir."""
    if not recorrente.ativo:
        return []

    hoje = date.today()
    proxima = (
        _primeira_data(recorrente.data_inicio, recorrente.dia_vencimento)
        if recorrente.ultima_geracao is None
        else _proximo_mes(recorrente.ultima_geracao, recorrente.dia_vencimento)
    )

    gerados: list[DespesaLancamento] = []
    for _ in range(_MAX_COMPETENCIAS_POR_CHAMADA):
        if proxima > hoje:
            break
        if recorrente.data_fim is not None and proxima > recorrente.data_fim:
            break

        lancamento = DespesaLancamento(
            predio_id=recorrente.predio_id,
            fornecedor_id=recorrente.fornecedor_id,
            unidade_id=recorrente.unidade_id,
            despesa_recorrente_id=recorrente.id,
            descricao=recorrente.descricao,
            categoria=recorrente.categoria,
            valor=recorrente.valor,
            data_vencimento=proxima,
            observacoes=recorrente.observacoes,
            status=StatusDespesaEnum.PENDENTE,
            created_by=recorrente.created_by,
        )
        db.add(lancamento)
        gerados.append(lancamento)

        recorrente.ultima_geracao = proxima
        proxima = _proximo_mes(proxima, recorrente.dia_vencimento)

    if gerados:
        db.add(recorrente)
    return gerados


def gerar_pendentes_do_predio(db: Session, predio_id: int) -> list[DespesaLancamento]:
    recorrentes = (
        db.query(DespesaRecorrente)
        .filter(
            DespesaRecorrente.predio_id == predio_id,
            DespesaRecorrente.deleted_at.is_(None),
            DespesaRecorrente.ativo.is_(True),
        )
        .all()
    )
    gerados: list[DespesaLancamento] = []
    for recorrente in recorrentes:
        gerados.extend(gerar_pendentes(db, recorrente))
    return gerados
