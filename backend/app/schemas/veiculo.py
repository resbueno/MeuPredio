from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TipoVeiculoEnum


class VeiculoBase(BaseModel):
    unidade_id: int
    placa: str = Field(min_length=6, max_length=10)
    modelo: str = Field(min_length=1, max_length=100)
    cor: str = Field(min_length=1, max_length=40)
    tipo: TipoVeiculoEnum = TipoVeiculoEnum.CARRO

    @field_validator("placa")
    @classmethod
    def normalizar_placa(cls, v: str) -> str:
        return v.strip().upper().replace(" ", "")


class VeiculoCreate(VeiculoBase):
    pass


class VeiculoUpdate(BaseModel):
    unidade_id: int | None = None
    placa: str | None = Field(default=None, min_length=6, max_length=10)
    modelo: str | None = Field(default=None, min_length=1, max_length=100)
    cor: str | None = Field(default=None, min_length=1, max_length=40)
    tipo: TipoVeiculoEnum | None = None

    @field_validator("placa")
    @classmethod
    def normalizar_placa(cls, v: str | None) -> str | None:
        return v.strip().upper().replace(" ", "") if v else v


class VeiculoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unidade_id: int
    placa: str
    modelo: str
    cor: str
    tipo: TipoVeiculoEnum
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
