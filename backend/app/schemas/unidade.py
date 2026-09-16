from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UnidadeBase(BaseModel):
    bloco: str = Field(min_length=1, max_length=20)
    numero: str = Field(min_length=1, max_length=20)
    proprietario_id: int | None = None


class UnidadeCreate(UnidadeBase):
    pass


class UnidadeUpdate(BaseModel):
    bloco: str | None = Field(default=None, min_length=1, max_length=20)
    numero: str | None = Field(default=None, min_length=1, max_length=20)
    proprietario_id: int | None = None


class UnidadeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bloco: str
    numero: str
    proprietario_id: int | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
