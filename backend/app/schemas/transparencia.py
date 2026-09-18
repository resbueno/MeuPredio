from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import StatusDespesaEnum


class DespesaTransparenciaRead(BaseModel):
    """Recorte publico de `DespesaLancamentoRead` para o Portal da
    Transparencia - sem `observacoes` (pode conter anotacao interna do
    sindico) nem `fornecedor_id`/auditoria, ja que aqui quem le e qualquer
    condomino do predio, nao so ADMINISTRADOR/SINDICO."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    unidade_id: int | None
    descricao: str
    categoria: str
    valor: Decimal
    data_vencimento: date
    data_pagamento: date | None
    status: StatusDespesaEnum
    esta_atrasada: bool
    documento_url: str | None
    comprovante_pagamento_url: str | None

    @field_validator("valor")
    @classmethod
    def _duas_casas(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class TotalPorCategoria(BaseModel):
    categoria: str
    total: Decimal

    @field_validator("total")
    @classmethod
    def _duas_casas(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class BalanceteResponse(BaseModel):
    """Prestacao de contas agregada de um periodo (ano, ou ano+mes) - soma
    por status e por categoria dos lancamentos com vencimento no periodo."""

    ano: int
    mes: int | None
    total_pago: Decimal
    total_pendente: Decimal
    total_cancelado: Decimal
    total_geral: Decimal
    por_categoria: list[TotalPorCategoria]

    @field_validator("total_pago", "total_pendente", "total_cancelado", "total_geral")
    @classmethod
    def _duas_casas(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class BalanceteMensal(BaseModel):
    """Um ponto da serie mensal (ver GET /transparencia/balancete/serie) -
    mesmos totais do BalanceteResponse, sem o detalhamento por categoria
    (o grafico de tendencia so precisa do total)."""

    ano: int
    mes: int
    total_pago: Decimal
    total_pendente: Decimal
    total_geral: Decimal

    @field_validator("total_pago", "total_pendente", "total_geral")
    @classmethod
    def _duas_casas(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class PreviaUnidadeItem(BaseModel):
    despesa_id: int
    descricao: str
    categoria: str
    tipo: str  # "rateio" (parte de uma despesa geral) ou "multa" (exclusiva da unidade)
    valor: Decimal
    status: StatusDespesaEnum
    data_vencimento: date

    @field_validator("valor")
    @classmethod
    def _duas_casas(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class PreviaUnidadeResponse(BaseModel):
    """Previa da conta de condominio de UMA unidade num periodo: a fatia
    dela nas despesas gerais ratejadas + qualquer despesa exclusiva sua
    (multa) - ver DespesaLancamento.unidade_id."""

    unidade_id: int
    ano: int
    mes: int | None
    total_rateio: Decimal
    total_multas: Decimal
    total_geral: Decimal
    itens: list[PreviaUnidadeItem]

    @field_validator("total_rateio", "total_multas", "total_geral")
    @classmethod
    def _duas_casas(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))
