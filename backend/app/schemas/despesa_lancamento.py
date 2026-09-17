from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import StatusDespesaEnum


class DespesaLancamentoBase(BaseModel):
    fornecedor_id: int | None = None
    descricao: str = Field(min_length=2, max_length=255)
    categoria: str = Field(min_length=2, max_length=100)
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    data_vencimento: date
    observacoes: str | None = None


class DespesaLancamentoCreate(DespesaLancamentoBase):
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    # Qualquer outro criador (síndico) tem o prédio forçado para o seu
    # próprio pelo router - nunca confia em predio_id vindo do cliente.
    predio_id: int | None = None


class DespesaLancamentoUpdate(BaseModel):
    fornecedor_id: int | None = None
    descricao: str | None = Field(default=None, min_length=2, max_length=255)
    categoria: str | None = Field(default=None, min_length=2, max_length=100)
    valor: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    data_vencimento: date | None = None
    observacoes: str | None = None


class DespesaLancamentoRegistrarPagamento(BaseModel):
    """Payload dedicado para dar baixa em um lançamento (transição de status
    controlada, em vez de deixar `status` livre em um PATCH genérico)."""

    data_pagamento: date = Field(default_factory=date.today)


class DespesaLancamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    fornecedor_id: int | None
    descricao: str
    categoria: str
    valor: Decimal
    data_vencimento: date
    data_pagamento: date | None
    status: StatusDespesaEnum
    esta_atrasada: bool
    documento_url: str | None
    observacoes: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @field_validator("valor")
    @classmethod
    def _duas_casas(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))
