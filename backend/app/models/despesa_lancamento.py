from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin
from app.models.enums import StatusDespesaEnum

if TYPE_CHECKING:
    from app.models.fornecedor import Fornecedor


class DespesaLancamento(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Lançamento de despesa do condomínio (Despesas_Lancamentos, Fase 2).

    Nesta fatia inicial do Motor Financeiro é só o registro/CRUD do
    lançamento — ainda sem rateio entre unidades, sem OCR (Mistral AI) e sem
    geração de remessa/retorno bancário, que ficam para as próximas fatias
    da Fase 2. `documento_url` já existe como campo para não exigir uma
    migration extra quando o pipeline de OCR chegar.
    """

    __tablename__ = "despesas_lancamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    fornecedor_id: Mapped[int | None] = mapped_column(
        ForeignKey("fornecedores.id", ondelete="SET NULL"), nullable=True
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_pagamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[StatusDespesaEnum] = mapped_column(
        SAEnum(
            StatusDespesaEnum,
            name="status_despesa_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=StatusDespesaEnum.PENDENTE,
    )
    documento_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    fornecedor: Mapped["Fornecedor | None"] = relationship(
        "Fornecedor", back_populates="despesas"
    )

    @property
    def esta_atrasada(self) -> bool:
        """Derivado, não persistido: pendente com vencimento no passado."""
        if self.status != StatusDespesaEnum.PENDENTE:
            return False
        hoje = datetime.now(timezone.utc).date()
        return self.data_vencimento < hoje

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DespesaLancamento id={self.id} descricao={self.descricao!r} valor={self.valor}>"
