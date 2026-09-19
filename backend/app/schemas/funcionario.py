from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _normalizar_cpf(v: str | None) -> str | None:
    if v is None:
        return None
    digitos = re.sub(r"\D", "", v)
    if not digitos:
        return None
    if len(digitos) != 11:
        raise ValueError("CPF deve ter 11 dígitos.")
    return digitos


class FuncionarioCreate(BaseModel):
    nome_completo: str = Field(min_length=2, max_length=255)
    cargo: str = Field(min_length=2, max_length=100)
    cpf: str | None = Field(default=None, max_length=14)
    telefone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    data_admissao: date | None = None
    salario: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    observacoes: str | None = Field(default=None, max_length=2000)

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str | None) -> str | None:
        return _normalizar_cpf(v)


class FuncionarioAtualizar(BaseModel):
    nome_completo: str | None = Field(default=None, min_length=2, max_length=255)
    cargo: str | None = Field(default=None, min_length=2, max_length=100)
    cpf: str | None = Field(default=None, max_length=14)
    telefone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    data_admissao: date | None = None
    salario: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    ativo: bool | None = None
    observacoes: str | None = Field(default=None, max_length=2000)

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str | None) -> str | None:
        return _normalizar_cpf(v)


class FuncionarioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    nome_completo: str
    cargo: str
    cpf: str | None
    telefone: str | None
    email: str | None
    data_admissao: date | None
    salario: Decimal | None
    ativo: bool
    observacoes: str | None
    created_at: datetime
    updated_at: datetime
