from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusReservaEnum


class ReservaCreate(BaseModel):
    area_comum_id: int
    data: date
    observacoes: str | None = Field(default=None, max_length=2000)
    # Só usado pela gestão, para reservar em nome de uma unidade que não é
    # a própria (ver RBAC no router) - morador/proprietário sempre reserva
    # para a própria unidade, ignorando este campo se enviado.
    unidade_id: int | None = None
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    predio_id: int | None = None


class ReservaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    area_comum_id: int
    unidade_id: int
    data: date
    status: StatusReservaEnum
    observacoes: str | None
    cancelada_em: datetime | None
    cancelada_por: int | None
    created_by: int | None
    created_at: datetime
