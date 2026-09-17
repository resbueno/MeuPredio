from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin
from app.models.enums import CriterioRateioEnum

if TYPE_CHECKING:
    from app.models.despesa_lancamento import DespesaLancamento


class RateioDespesaItem(Base, TimestampMixin, AuditMixin):
    """A fatia de uma despesa atribuída a uma unidade específica, calculada
    pelo motor de rateio (ver POST /despesas/{id}/ratear).

    Sem `SoftDeleteMixin` de propósito: um recálculo de rateio substitui o
    conjunto de itens inteiro (delete + insert na mesma transação) em vez de
    acumular histórico aqui — quem precisar do histórico de recálculos
    consulta `logs_auditoria` (ação `RATEIO`).
    """

    __tablename__ = "rateio_despesa_itens"
    __table_args__ = (
        UniqueConstraint("despesa_lancamento_id", "unidade_id", name="uq_rateio_despesa_unidade"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    despesa_lancamento_id: Mapped[int] = mapped_column(
        ForeignKey("despesas_lancamentos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    criterio: Mapped[CriterioRateioEnum] = mapped_column(
        SAEnum(
            CriterioRateioEnum,
            name="criterio_rateio_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )

    despesa: Mapped["DespesaLancamento"] = relationship(
        "DespesaLancamento", back_populates="itens_rateio"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<RateioDespesaItem despesa_id={self.despesa_lancamento_id} "
            f"unidade_id={self.unidade_id} valor={self.valor}>"
        )
