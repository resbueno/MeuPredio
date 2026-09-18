from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OcorrenciaCreate(BaseModel):
    titulo: str = Field(min_length=2, max_length=200)
    descricao: str = Field(min_length=2, max_length=4000)
    unidade_id: int | None = None
    predio_id: int | None = None


class OcorrenciaAtualizar(BaseModel):
    """Só o síndico/administrador usa (ver RBAC no router) - marca
    `editado_em`/`editado_por` sempre que aplicada."""

    titulo: str | None = Field(default=None, min_length=2, max_length=200)
    descricao: str | None = Field(default=None, min_length=2, max_length=4000)


class OcorrenciaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    unidade_id: int | None
    titulo: str
    descricao: str
    editado_em: datetime | None
    editado_por: int | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime
