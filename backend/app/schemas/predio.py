from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import validar_senha_forte
from app.core.viacep import normalizar_cep
from app.models.enums import ModuloEnum


class UnidadeInicial(BaseModel):
    """Uma unidade informada no momento da criação do prédio (bulk)."""

    bloco: str = Field(min_length=1, max_length=20)
    numero: str = Field(min_length=1, max_length=20)


class PredioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=255)
    cep: str = Field(min_length=8, max_length=9)
    numero: str = Field(min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=100)
    unidades: list[UnidadeInicial] = Field(default_factory=list)
    # list(ModuloEnum), não TODOS_MODULOS (que é list[str]) - default_factory
    # não passa pela coerção normal do Pydantic, então precisa já devolver
    # instâncias de ModuloEnum (com `.value`), não strings soltas, ou
    # `criar_predio` quebra ao tentar `m.value` em cada item da lista.
    modulos_habilitados: list[ModuloEnum] = Field(default_factory=lambda: list(ModuloEnum))

    @field_validator("cep")
    @classmethod
    def validar_cep(cls, v: str) -> str:
        return normalizar_cep(v)


class PredioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cep: str
    numero: str
    complemento: str | None
    logradouro: str | None
    bairro: str | None
    cidade: str | None
    uf: str | None
    modulos_habilitados: list[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class PredioAtualizar(BaseModel):
    """Payload de `PATCH /predios/{id}`: só os campos enviados são
    alterados (`exclude_unset`). Mudar `cep`/`numero` refaz a consulta ao
    ViaCEP (endereço é recalculado) e reconfere a unicidade do par."""

    nome: str | None = Field(default=None, min_length=2, max_length=255)
    cep: str | None = Field(default=None, min_length=8, max_length=9)
    numero: str | None = Field(default=None, min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=100)

    @field_validator("cep")
    @classmethod
    def validar_cep(cls, v: str | None) -> str | None:
        return normalizar_cep(v) if v is not None else v


class PredioModulosUpdate(BaseModel):
    """Payload de `PUT /predios/{id}/modulos`: substitui por completo a
    lista de módulos habilitados do prédio (não é um patch incremental)."""

    modulos_habilitados: list[ModuloEnum]


class PredioIdentificarRequest(BaseModel):
    """Payload da 1a etapa do login: identificar o prédio por CEP + número
    do endereço, antes de pedir e-mail/senha."""

    cep: str = Field(min_length=8, max_length=9)
    numero: str = Field(min_length=1, max_length=20)

    @field_validator("cep")
    @classmethod
    def validar_cep(cls, v: str) -> str:
        return normalizar_cep(v)


class PredioIdentificarResponse(BaseModel):
    id: int
    nome: str
    cidade: str | None
    uf: str | None


class PredioConviteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    predio_id: int
    token: str
    ativo: bool
    expira_em: date | None
    esta_valido: bool


class UnidadeConviteInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bloco: str
    numero: str


class PredioConviteInfo(BaseModel):
    """O que a tela pública de autocadastro (`GET /predios/convite/{token}`)
    pode ver: dados do prédio e a lista de unidades - nada de dados de outros
    usuários/prédios."""

    predio_nome: str
    predio_id: int
    unidades: list[UnidadeConviteInfo]


class PredioIntegracaoOcrRequest(BaseModel):
    """Configura a chave de API do Groq deste prédio (OCR de boletos) -
    deve ser uma conta/chave do próprio condomínio, não uma chave global do
    sistema (cada prédio paga/gerencia seu próprio uso)."""

    groq_api_key: str = Field(min_length=10, max_length=200)


class PredioIntegracaoOcrStatus(BaseModel):
    """Nunca devolve a chave em si (nem cifrada, nem parcialmente) - só se
    está configurada ou não."""

    configurado: bool


class CadastroViaConviteRequest(BaseModel):
    """Autocadastro público (`POST /predios/convite/{token}/cadastro`).

    Restrito aos papéis "residentes" (morador/proprietário) — síndico,
    zelador e administrador continuam sendo criados/promovidos por quem já
    tem acesso ao sistema (ver POST /usuarios), nunca por um link público.
    """

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
    role: Literal["morador", "proprietario"]
    unidade_ids: list[int] = Field(min_length=1)

    @field_validator("password")
    @classmethod
    def senha_deve_ser_forte(cls, v: str) -> str:
        erro = validar_senha_forte(v)
        if erro:
            raise ValueError(erro)
        return v
