from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EntregaCreate(BaseModel):
    unidade_id: int
    descricao: str = Field(min_length=2, max_length=255)
    localizacao: str = Field(min_length=2, max_length=255)
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    predio_id: int | None = None


class EntregaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    unidade_id: int
    descricao: str
    localizacao: str
    retirada_em: datetime | None
    retirada_por: int | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime
