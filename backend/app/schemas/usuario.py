from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.enums import RoleEnum


class UsuarioBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    role: RoleEnum = RoleEnum.MORADOR
    unidade_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def _exigir_unidade_exceto_administrador(self) -> "UsuarioBase":
        if self.role != RoleEnum.ADMINISTRADOR and not self.unidade_ids:
            raise ValueError(
                "Todo usuario (exceto administrador) deve estar vinculado a pelo menos uma unidade."
            )
        if self.role == RoleEnum.ADMINISTRADOR and self.unidade_ids:
            raise ValueError("Administrador e um papel global e nao pode estar vinculado a unidades.")
        return self


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=8, max_length=128)
    # Só usado quando quem cria é o ADMINISTRADOR (sem prédio próprio) e
    # precisa dizer para qual prédio este usuário vai. Para qualquer outro
    # criador (síndico, p.ex.), o router ignora este campo e força o prédio
    # do próprio criador — nunca confia em predio_id vindo do cliente para
    # decidir isolamento entre tenants.
    predio_id: int | None = None

    @field_validator("password")
    @classmethod
    def senha_deve_ser_forte(cls, v: str) -> str:
        if v.isdigit() or v.isalpha():
            raise ValueError(
                "A senha deve ter ao menos 8 caracteres combinando letras e numeros."
            )
        return v


class UsuarioUpdate(BaseModel):
    """Todos os campos são opcionais (PATCH); o router decide, por RBAC,
    quais campos cada papel pode de fato alterar."""

    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    role: RoleEnum | None = None
    unidade_ids: list[int] | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def senha_deve_ser_forte(cls, v: str | None) -> str | None:
        if v is not None and (v.isdigit() or v.isalpha()):
            raise ValueError(
                "A senha deve ter ao menos 8 caracteres combinando letras e numeros."
            )
        return v


class UsuarioRead(BaseModel):
    """Schema de LEITURA: `email` aqui é `str`, não `EmailStr`, de propósito.

    `EmailStr` (via email-validator) rejeita domínios "special-use" (.local,
    .invalid, .test, .example, RFC 6761/2606) mesmo em modo leitura — isso já
    causou um 500 (ResponseValidationError) em produção/homologação com o
    e-mail do admin semeado (admin@meupredio.local) e quebra a própria rota
    de anonimização LGPD, que grava deliberadamente
    `anonimizado-{id}@meupredio.invalid`. Validar de novo no READ um dado que
    já foi validado (ou gerado pelo próprio sistema) no CREATE não tem
    utilidade e só cria uma superfície de 500 fora do nosso controle. A
    validação estrita continua em `UsuarioBase.email` (Create/Update), onde
    de fato importa rejeitar entrada nova inválida."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: RoleEnum
    predio_id: int | None
    unidade_ids: list[int] = Field(default_factory=list)
    is_active: bool
    consent_lgpd_accepted_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    anonymized_at: datetime | None

    @model_validator(mode="before")
    @classmethod
    def _extrair_unidade_ids(cls, obj):
        # `obj` é o próprio ORM `Usuario` (from_attributes) - `unidade_ids`
        # não existe como coluna, é derivado da relação N:N `unidades`.
        if hasattr(obj, "unidades") and not isinstance(obj, dict):
            unidades = obj.unidades
            data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
            data["unidade_ids"] = [u.id for u in unidades]
            return data
        return obj
