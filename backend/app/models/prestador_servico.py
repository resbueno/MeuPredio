from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.predio import Predio


class PrestadorServico(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Empresa/pessoa contratada para um serviço recorrente do condomínio
    (limpeza, elevadores, jardinagem...), com o custo mensal do contrato.

    `incluir_no_rateio` decide se esse custo é repassado às unidades: ligado,
    o lançamento do custo (POST /prestadores-servico/{id}/lancar-custo) já
    nasce rateado pelo `criterio_rateio`; desligado, vira só uma despesa do
    condomínio (aparece no balancete, mas não gera cobrança por unidade).
    Distinto de `Fornecedor` (diretório financeiro usado por boletos/contas,
    acessível também ao administrador) - este é o cadastro operacional da
    equipe, restrito a síndico/zelador.
    """

    __tablename__ = "prestadores_servico"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_servico: Mapped[str] = mapped_column(String(100), nullable=False)
    razao_social: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cnpj: Mapped[str | None] = mapped_column(String(14), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custo_mensal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    incluir_no_rateio: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # "igual" | "fracao_ideal" (valores de CriterioRateioEnum) - texto, e não
    # o enum nativo do Postgres, para não compartilhar o tipo com o rateio.
    criterio_rateio: Mapped[str] = mapped_column(String(20), nullable=False, default="igual")
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    predio: Mapped["Predio"] = relationship("Predio")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PrestadorServico id={self.id} nome={self.nome!r} custo={self.custo_mensal}>"
