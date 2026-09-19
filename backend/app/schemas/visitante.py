from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import TipoDocumentoVisitanteEnum


class VisitanteCreate(BaseModel):
    unidade_id: int
    nome_completo: str = Field(min_length=2, max_length=255)
    tipo_documento: TipoDocumentoVisitanteEnum
    numero_documento: str | None = Field(default=None, max_length=50)
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio).
    predio_id: int | None = None

    @model_validator(mode="after")
    def validar_documento(self) -> "VisitanteCreate":
        informado = self.numero_documento is not None and self.numero_documento.strip() != ""
        if self.tipo_documento == TipoDocumentoVisitanteEnum.NAO_INFORMADO and informado:
            raise ValueError("Não informe número de documento quando o tipo for 'não informado'.")
        if self.tipo_documento != TipoDocumentoVisitanteEnum.NAO_INFORMADO and not informado:
            raise ValueError("Informe o número do documento, ou selecione o tipo 'não informado'.")
        return self


class VisitanteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    unidade_id: int
    nome_completo: str
    tipo_documento: TipoDocumentoVisitanteEnum
    numero_documento: str | None
    created_by: int | None
    created_at: datetime
