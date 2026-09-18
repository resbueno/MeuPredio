from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TipoAvisoMuralEnum


class AvisoMuralCreate(BaseModel):
    tipo: TipoAvisoMuralEnum
    titulo: str = Field(min_length=2, max_length=200)
    descricao: str = Field(min_length=2, max_length=4000)
    preco: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    predio_id: int | None = None


class AvisoMuralAtualizar(BaseModel):
    titulo: str | None = Field(default=None, min_length=2, max_length=200)
    descricao: str | None = Field(default=None, min_length=2, max_length=4000)
    preco: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)


class AvisoMuralRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    tipo: TipoAvisoMuralEnum
    titulo: str
    descricao: str
    preco: Decimal | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    @field_validator("preco")
    @classmethod
    def _duas_casas(cls, v: Decimal | None) -> Decimal | None:
        return v.quantize(Decimal("0.01")) if v is not None else v
