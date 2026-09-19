from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class UnidadeBase(BaseModel):
    bloco: str = Field(min_length=1, max_length=20)
    numero: str = Field(min_length=1, max_length=20)


class UnidadeCreate(UnidadeBase):
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    # Qualquer outro criador tem o prédio forçado para o seu próprio pelo
    # router - nunca confia em predio_id vindo do cliente.
    predio_id: int | None = None
    # Peso usado pelo motor de rateio quando o critério é "fracao_ideal" -
    # ver Unidade.fracao_ideal.
    fracao_ideal: Decimal | None = Field(default=None, gt=0, max_digits=9, decimal_places=6)
    vaga: str | None = Field(default=None, max_length=20)


class UnidadeLoteItem(UnidadeBase):
    fracao_ideal: Decimal | None = Field(default=None, gt=0, max_digits=9, decimal_places=6)
    vaga: str | None = Field(default=None, max_length=20)


class UnidadeLoteCreate(BaseModel):
    """Cadastro em lote (ex.: um bloco inteiro de uma vez) - o cliente monta
    a lista final de bloco/número (a numeração por andar é decidida na UI,
    o backend só valida e insere tudo de uma vez, tudo ou nada)."""

    unidades: list[UnidadeLoteItem] = Field(min_length=1, max_length=500)
    predio_id: int | None = None


class UnidadeUpdate(BaseModel):
    bloco: str | None = Field(default=None, min_length=1, max_length=20)
    numero: str | None = Field(default=None, min_length=1, max_length=20)
    fracao_ideal: Decimal | None = Field(default=None, gt=0, max_digits=9, decimal_places=6)
    vaga: str | None = Field(default=None, max_length=20)


class UnidadeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    bloco: str
    numero: str
    fracao_ideal: Decimal | None
    vaga: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
