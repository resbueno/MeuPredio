"""Aplica o rateio de um `DespesaLancamento` entre as unidades ativas do
prédio - compartilhado entre POST /despesas/{id}/ratear e o lançamento do
custo de um prestador de serviço (ver routers/prestadores_servico.py), para
as duas rotas nunca divergirem nas regras."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.rateio import calcular_rateio
from app.models.despesa_lancamento import DespesaLancamento
from app.models.enums import CriterioRateioEnum
from app.models.rateio_despesa_item import RateioDespesaItem
from app.models.unidade import Unidade


def aplicar_rateio(
    db: Session,
    despesa: DespesaLancamento,
    criterio: CriterioRateioEnum,
    usuario_id: int,
) -> list[RateioDespesaItem]:
    """Substitui (nunca acumula) os itens de rateio da despesa. Não comita
    nem valida status - quem chama decide (ver `_exigir_pendente`)."""
    if despesa.unidade_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta despesa é exclusiva de uma unidade e não pode ser rateada entre todas.",
        )

    unidades = (
        db.query(Unidade)
        .filter(Unidade.predio_id == despesa.predio_id, Unidade.deleted_at.is_(None))
        .order_by(Unidade.id)
        .all()
    )
    if not unidades:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nenhuma unidade ativa neste prédio para ratear.",
        )

    if criterio == CriterioRateioEnum.FRACAO_IDEAL:
        sem_fracao = [u.id for u in unidades if not u.fracao_ideal or u.fracao_ideal <= 0]
        if sem_fracao:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "Todas as unidades ativas precisam ter fracao_ideal definida (>0) "
                    f"para ratear por fração ideal. Unidade(s) sem fracao_ideal: {sem_fracao}."
                ),
            )
        pesos = [(u.id, u.fracao_ideal) for u in unidades]
    else:
        pesos = [(u.id, Decimal(1)) for u in unidades]

    valores_por_unidade = calcular_rateio(despesa.valor, pesos)

    db.query(RateioDespesaItem).filter(
        RateioDespesaItem.despesa_lancamento_id == despesa.id
    ).delete(synchronize_session=False)

    itens_novos: list[RateioDespesaItem] = []
    for unidade_id, valor_unidade in valores_por_unidade.items():
        item = RateioDespesaItem(
            predio_id=despesa.predio_id,
            despesa_lancamento_id=despesa.id,
            unidade_id=unidade_id,
            valor=valor_unidade,
            criterio=criterio,
            created_by=usuario_id,
        )
        db.add(item)
        itens_novos.append(item)

    despesa.rateado_em = datetime.now(timezone.utc)
    db.add(despesa)
    db.flush()
    return itens_novos
