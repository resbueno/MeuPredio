from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DespesaRecorrenteCreate(BaseModel):
    fornecedor_id: int | None = None
    unidade_id: int | None = None
    descricao: str = Field(min_length=2, max_length=255)
    categoria: str = Field(min_length=2, max_length=100)
    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    dia_vencimento: int = Field(ge=1, le=28)
    data_inicio: date = Field(default_factory=date.today)
    data_fim: date | None = None
    observacoes: str | None = None
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    predio_id: int | None = None


class DespesaRecorrenteAtualizar(BaseModel):
    fornecedor_id: int | None = None
    unidade_id: int | None = None
    descricao: str | None = Field(default=None, min_length=2, max_length=255)
    categoria: str | None = Field(default=None, min_length=2, max_length=100)
    valor: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    dia_vencimento: int | None = Field(default=None, ge=1, le=28)
    ativo: bool | None = None
    data_fim: date | None = None
    observacoes: str | None = None


class DespesaRecorrenteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    fornecedor_id: int | None
    unidade_id: int | None
    descricao: str
    categoria: str
    valor: Decimal
    dia_vencimento: int
    ativo: bool
    data_inicio: date
    data_fim: date | None
    ultima_geracao: date | None
    observacoes: str | None
    created_at: datetime
    updated_at: datetime
