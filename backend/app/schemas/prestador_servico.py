from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import CriterioRateioEnum


def _normalizar_cnpj(v: str | None) -> str | None:
    if v is None:
        return None
    digitos = re.sub(r"\D", "", v)
    if not digitos:
        return None
    if len(digitos) != 14:
        raise ValueError("CNPJ deve ter 14 dígitos.")
    return digitos


class PrestadorServicoCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=255)
    tipo_servico: str = Field(min_length=2, max_length=100)
    razao_social: str | None = Field(default=None, max_length=255)
    cnpj: str | None = Field(default=None, max_length=18)
    telefone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    custo_mensal: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    incluir_no_rateio: bool = False
    criterio_rateio: CriterioRateioEnum = CriterioRateioEnum.IGUAL
    observacoes: str | None = Field(default=None, max_length=2000)

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str | None) -> str | None:
        return _normalizar_cnpj(v)


class PrestadorServicoAtualizar(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=255)
    tipo_servico: str | None = Field(default=None, min_length=2, max_length=100)
    razao_social: str | None = Field(default=None, max_length=255)
    cnpj: str | None = Field(default=None, max_length=18)
    telefone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    custo_mensal: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    incluir_no_rateio: bool | None = None
    criterio_rateio: CriterioRateioEnum | None = None
    ativo: bool | None = None
    observacoes: str | None = Field(default=None, max_length=2000)

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str | None) -> str | None:
        return _normalizar_cnpj(v)


class PrestadorServicoLancarCusto(BaseModel):
    data_vencimento: date
    observacoes: str | None = Field(default=None, max_length=2000)


class PrestadorServicoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    nome: str
    tipo_servico: str
    razao_social: str | None
    cnpj: str | None
    telefone: str | None
    email: str | None
    custo_mensal: Decimal
    incluir_no_rateio: bool
    criterio_rateio: str
    ativo: bool
    observacoes: str | None
    created_at: datetime
    updated_at: datetime
