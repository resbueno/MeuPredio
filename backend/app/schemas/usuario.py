from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import RoleEnum


class UsuarioBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    role: RoleEnum = RoleEnum.MORADOR
    unidade_id: int | None = None


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=8, max_length=128)

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
    unidade_id: int | None = None
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
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: RoleEnum
    unidade_id: int | None
    is_active: bool
    consent_lgpd_accepted_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    anonymized_at: datetime | None
