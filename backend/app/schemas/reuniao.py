from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusReuniaoEnum, TipoReuniaoEnum


class ReuniaoCreate(BaseModel):
    tipo: TipoReuniaoEnum
    titulo: str = Field(min_length=2, max_length=200)
    data_hora: datetime
    local: str = Field(min_length=2, max_length=255)
    pauta: str = Field(min_length=2, max_length=4000)
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    predio_id: int | None = None


class ReuniaoAtualizar(BaseModel):
    """Só enquanto `status == 'convocada'` (ver `_exigir_convocada` no
    router) - depois de realizada ou cancelada, a convocação já foi
    publicada e não se edita mais silenciosamente."""

    tipo: TipoReuniaoEnum | None = None
    titulo: str | None = Field(default=None, min_length=2, max_length=200)
    data_hora: datetime | None = None
    local: str | None = Field(default=None, min_length=2, max_length=255)
    pauta: str | None = Field(default=None, min_length=2, max_length=4000)


class ReuniaoAtaInput(BaseModel):
    ata: str = Field(min_length=2, max_length=8000)


class PresencaCreate(BaseModel):
    unidade_id: int


class PresencaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reuniao_id: int
    unidade_id: int
    created_by: int | None
    created_at: datetime


class ReuniaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    tipo: TipoReuniaoEnum
    status: StatusReuniaoEnum
    titulo: str
    data_hora: datetime
    local: str
    pauta: str
    ata: str | None
    ata_registrada_em: datetime | None
    ata_registrada_por: int | None
    created_by: int | None
    presencas: list[PresencaRead] = []
    created_at: datetime
    updated_at: datetime
