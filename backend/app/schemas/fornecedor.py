from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_DOCUMENTO_RE = re.compile(r"^\d{11}$|^\d{14}$")  # CPF (11 dígitos) ou CNPJ (14 dígitos)
_CNPJ_RE = re.compile(r"^\d{14}$")


def _normalizar_documento(v: str | None) -> str | None:
    if v is None:
        return None
    apenas_digitos = re.sub(r"\D", "", v)
    if not apenas_digitos:
        return None
    if not _DOCUMENTO_RE.match(apenas_digitos):
        raise ValueError("Documento deve ser um CPF (11 digitos) ou CNPJ (14 digitos) validos.")
    return apenas_digitos


def _normalizar_cnpj(v: str | None) -> str | None:
    if v is None:
        return None
    apenas_digitos = re.sub(r"\D", "", v)
    if not apenas_digitos:
        return None
    if not _CNPJ_RE.match(apenas_digitos):
        raise ValueError("CNPJ deve ter 14 dígitos.")
    return apenas_digitos


class FornecedorBase(BaseModel):
    nome: str = Field(min_length=2, max_length=255)
    documento: str | None = Field(default=None, max_length=20)
    cnpj: str | None = Field(default=None, max_length=18)
    razao_social: str | None = Field(default=None, max_length=255)
    nome_fantasia: str | None = Field(default=None, max_length=255)
    categoria: str = Field(min_length=2, max_length=100)
    telefone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    observacoes: str | None = None

    @field_validator("documento")
    @classmethod
    def validar_documento(cls, v: str | None) -> str | None:
        return _normalizar_documento(v)

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str | None) -> str | None:
        return _normalizar_cnpj(v)


class FornecedorCreate(FornecedorBase):
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    # Qualquer outro criador (síndico) tem o prédio forçado para o seu
    # próprio pelo router - nunca confia em predio_id vindo do cliente.
    predio_id: int | None = None


class FornecedorUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=255)
    documento: str | None = Field(default=None, max_length=20)
    cnpj: str | None = Field(default=None, max_length=18)
    razao_social: str | None = Field(default=None, max_length=255)
    nome_fantasia: str | None = Field(default=None, max_length=255)
    categoria: str | None = Field(default=None, min_length=2, max_length=100)
    telefone: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    observacoes: str | None = None

    @field_validator("documento")
    @classmethod
    def validar_documento(cls, v: str | None) -> str | None:
        return _normalizar_documento(v)

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str | None) -> str | None:
        return _normalizar_cnpj(v)


class FornecedorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    nome: str
    documento: str | None
    cnpj: str | None
    razao_social: str | None
    nome_fantasia: str | None
    categoria: str
    telefone: str | None
    email: str | None
    observacoes: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
