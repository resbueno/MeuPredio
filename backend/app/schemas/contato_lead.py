from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContatoLeadCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=255)
    email: EmailStr
    telefone: str | None = Field(default=None, max_length=20)
    mensagem: str | None = Field(default=None, max_length=2000)


class ContatoLeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    telefone: str | None
    mensagem: str | None
    atendido: bool
    created_at: datetime
