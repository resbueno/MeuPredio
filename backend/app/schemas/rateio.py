from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import CriterioRateioEnum


class RatearDespesaRequest(BaseModel):
    """Critério exigido explicitamente (sem default silencioso): quem
    ratear uma despesa financeira precisa escolher conscientemente entre
    dividir igualmente ou por fração ideal."""

    criterio: CriterioRateioEnum


class RateioDespesaItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    despesa_lancamento_id: int
    unidade_id: int
    valor: Decimal
    criterio: CriterioRateioEnum
    created_at: datetime

    @field_validator("valor")
    @classmethod
    def _duas_casas(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))
