from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import TipoNotificacaoEnum


class NotificacaoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoNotificacaoEnum
    titulo: str
    mensagem: str
    referencia_tipo: str | None
    referencia_id: int | None
    lida_em: datetime | None
    created_at: datetime


class NotificacaoContagem(BaseModel):
    nao_lidas: int
