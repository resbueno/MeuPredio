from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_DOCUMENTO_RE = re.compile(r"^\d{11}$|^\d{14}$")  # CPF (11 dígitos) ou CNPJ (14 dígitos)


def _normalizar_documento(v: str | None) -> str | None:
    if v is None:
        return None
    apenas_digitos = re.sub(r"\D", "", v)
    if not apenas_digitos:
        return None
    if not _DOCUMENTO_RE.match(apenas_digitos):
        raise ValueError("Documento deve ser um CPF (11 digitos) ou CNPJ (14 digitos) validos.")
    return apenas_digitos


class FornecedorBase(BaseModel):
    nome: str = Field(min_length=2, max_length=255)
    documento: str | None = Field(default=None, max_length=20)
    categoria: str = Field(min_length=2, max_length=100)
    telefone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    observacoes: str | None = None

    @field_validator("documento")
    @classmethod
    def validar_documento(cls, v: str | None) -> str | None:
        return _normalizar_documento(v)


class FornecedorCreate(FornecedorBase):
    pass


class FornecedorUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=255)
    documento: str | None = Field(default=None, max_length=20)
    categoria: str | None = Field(default=None, min_length=2, max_length=100)
    telefone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    observacoes: str | None = None

    @field_validator("documento")
    @classmethod
    def validar_documento(cls, v: str | None) -> str | None:
        return _normalizar_documento(v)


class FornecedorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    documento: str | None
    categoria: str
    telefone: str | None
    email: str | None
    observacoes: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
