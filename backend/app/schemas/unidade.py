from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UnidadeBase(BaseModel):
    bloco: str = Field(min_length=1, max_length=20)
    numero: str = Field(min_length=1, max_length=20)


class UnidadeCreate(UnidadeBase):
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    # Qualquer outro criador tem o prédio forçado para o seu próprio pelo
    # router - nunca confia em predio_id vindo do cliente.
    predio_id: int | None = None


class UnidadeUpdate(BaseModel):
    bloco: str | None = Field(default=None, min_length=1, max_length=20)
    numero: str | None = Field(default=None, min_length=1, max_length=20)


class UnidadeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    bloco: str
    numero: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
