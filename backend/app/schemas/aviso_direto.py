from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import DestinatarioAvisoEnum, TipoAvisoDiretoEnum


class AvisoDiretoCreate(BaseModel):
    unidade_id: int
    destinatario: DestinatarioAvisoEnum
    tipo: TipoAvisoDiretoEnum
    titulo: str = Field(min_length=2, max_length=200)
    mensagem: str = Field(min_length=2, max_length=4000)
    # Obrigatorio quando tipo == MULTA (gera a despesa vinculada); ignorado
    # nos demais tipos - validado abaixo em vez de dois schemas separados,
    # ja que so esse campo muda de acordo com o tipo.
    valor: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    data_vencimento: date | None = None
    predio_id: int | None = None

    @model_validator(mode="after")
    def _valor_exigido_para_multa(self) -> "AvisoDiretoCreate":
        if self.tipo == TipoAvisoDiretoEnum.MULTA and (self.valor is None or self.data_vencimento is None):
            raise ValueError("Multa exige valor e data_vencimento.")
        return self


class AvisoDiretoResponder(BaseModel):
    resposta: str = Field(min_length=1, max_length=2000)


class AvisoDiretoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    unidade_id: int
    destinatario: DestinatarioAvisoEnum
    tipo: TipoAvisoDiretoEnum
    titulo: str
    mensagem: str
    valor: Decimal | None
    despesa_lancamento_id: int | None
    lida_em: datetime | None
    resposta: str | None
    respondido_por: int | None
    respondido_em: datetime | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    @field_validator("valor")
    @classmethod
    def _duas_casas(cls, v: Decimal | None) -> Decimal | None:
        return v.quantize(Decimal("0.01")) if v is not None else v
