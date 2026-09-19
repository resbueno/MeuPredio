from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AreaComumCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    descricao: str | None = Field(default=None, max_length=4000)
    capacidade: int | None = Field(default=None, gt=0)
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    predio_id: int | None = None


class AreaComumAtualizar(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=150)
    descricao: str | None = Field(default=None, max_length=4000)
    capacidade: int | None = Field(default=None, gt=0)
    ativo: bool | None = None


class AreaComumLiberarAgenda(BaseModel):
    """Exatamente um dos dois: `dias` conta a partir de hoje (ex.: 60 =
    próximos 60 dias), `ate` define a data-limite diretamente."""

    dias: int | None = Field(default=None, gt=0, le=730)
    ate: date | None = None

    @model_validator(mode="after")
    def validar_exclusividade(self) -> "AreaComumLiberarAgenda":
        if (self.dias is None) == (self.ate is None):
            raise ValueError("Informe exatamente um dos campos: 'dias' ou 'ate'.")
        return self


class AreaComumRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    nome: str
    descricao: str | None
    capacidade: int | None
    ativo: bool
    agenda_liberada_ate: date | None
    created_at: datetime
    updated_at: datetime
