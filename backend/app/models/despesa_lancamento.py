from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin
from app.models.enums import StatusDespesaEnum

if TYPE_CHECKING:
    from app.models.fornecedor import Fornecedor
    from app.models.rateio_despesa_item import RateioDespesaItem
    from app.models.unidade import Unidade


class DespesaLancamento(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Lançamento de despesa do condomínio (Despesas_Lancamentos, Fase 2).

    Segunda fatia do Motor Financeiro: CRUD do lançamento (fatia anterior)
    + rateio entre unidades (`itens_rateio`, ver POST /despesas/{id}/ratear).
    Ainda sem OCR (Mistral AI) e sem geração de remessa/retorno bancário, que
    ficam para as próximas fatias da Fase 2. `documento_url` já existe como
    campo para não exigir uma migration extra quando o pipeline de OCR
    chegar.
    """

    __tablename__ = "despesas_lancamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fornecedor_id: Mapped[int | None] = mapped_column(
        ForeignKey("fornecedores.id", ondelete="SET NULL"), nullable=True
    )
    # Preenchido só quando este lançamento foi gerado automaticamente a
    # partir de uma DespesaRecorrente (ver app/core/despesas_recorrentes.py)
    # - rastreabilidade, nunca usado para bloquear edição/exclusão manual.
    despesa_recorrente_id: Mapped[int | None] = mapped_column(
        ForeignKey("despesas_recorrentes.id", ondelete="SET NULL"), nullable=True
    )
    # Preenchido quando o lançamento veio do custo de um prestador de serviço
    # (ver routers/prestadores_servico.py) - rastreabilidade e trava contra
    # lançar o mesmo prestador duas vezes no mesmo mês.
    prestador_servico_id: Mapped[int | None] = mapped_column(
        ForeignKey("prestadores_servico.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Nulo (padrão): despesa geral do condomínio, ratejada entre as unidades
    # (`itens_rateio`). Preenchido: despesa EXCLUSIVA daquela unidade (ex.:
    # multa gerada por um aviso direto, ver models/aviso_direto.py) - nunca
    # pode ser rateada (ver guarda em POST /despesas/{id}/ratear) e só é
    # visível, no Portal da Transparência, a quem mora/é dono dela.
    unidade_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidades.id", ondelete="SET NULL"), nullable=True, index=True
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
    # Comprovante da baixa em si (recibo, print do PIX/TED) - distinto de
    # `documento_url` (o boleto original, anexado na criacao). Anexavel a
    # qualquer momento depois que o lancamento vira "pago", ver
    # POST /despesas/{id}/comprovante.
    comprovante_pagamento_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rateado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    fornecedor: Mapped["Fornecedor | None"] = relationship(
        "Fornecedor", back_populates="despesas"
    )
    unidade: Mapped["Unidade | None"] = relationship("Unidade")
    itens_rateio: Mapped[list["RateioDespesaItem"]] = relationship(
        "RateioDespesaItem", back_populates="despesa", order_by="RateioDespesaItem.unidade_id"
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
