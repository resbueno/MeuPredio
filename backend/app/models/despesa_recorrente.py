from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.fornecedor import Fornecedor
    from app.models.predio import Predio
    from app.models.unidade import Unidade


class DespesaRecorrente(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Modelo (template) de uma conta que se repete todo mês (água, luz,
    contrato de zeladoria...) - cadastrado uma vez pelo síndico/administrador
    para não precisar lançar manualmente o mesmo boleto todo mês (ver
    routers/despesas_recorrentes.py).

    `dia_vencimento` é limitado a 1-28 deliberadamente: todo mês tem pelo
    menos 28 dias, então a data de vencimento gerada nunca precisa de
    ajuste especial de "estoura o mês" (ex.: dia 31 em fevereiro).

    `ultima_geracao` é a data de vencimento do último `DespesaLancamento`
    já criado a partir deste modelo - fonte de verdade para saber a partir
    de onde continuar gerando (ver `app/core/despesas_recorrentes.py`),
    nunca recalculada a partir de "hoje" (evita pular ou duplicar um mês se
    a geração ficar um tempo sem rodar).
    """

    __tablename__ = "despesas_recorrentes"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fornecedor_id: Mapped[int | None] = mapped_column(
        ForeignKey("fornecedores.id", ondelete="SET NULL"), nullable=True
    )
    unidade_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidades.id", ondelete="SET NULL"), nullable=True
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    dia_vencimento: Mapped[int] = mapped_column(Integer, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fim: Mapped[date | None] = mapped_column(Date, nullable=True)
    ultima_geracao: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    predio: Mapped["Predio"] = relationship("Predio")
    fornecedor: Mapped["Fornecedor | None"] = relationship("Fornecedor")
    unidade: Mapped["Unidade | None"] = relationship("Unidade")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DespesaRecorrente id={self.id} descricao={self.descricao!r} dia_vencimento={self.dia_vencimento}>"
