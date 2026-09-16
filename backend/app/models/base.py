"""Mixins compartilhados pelos modelos ORM."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class TimestampMixin:
    """Carimbos de criação/atualização, gerados pelo próprio banco."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AuditMixin:
    """Referência a qual usuário criou o registro, para trilha de auditoria.

    Nullable porque o próprio primeiro administrador (seed) e operações de
    sistema não têm um usuário "autor" anterior.
    """

    @declared_attr
    def created_by(cls) -> Mapped[int | None]:
        return mapped_column(
            ForeignKey("usuarios.id", ondelete="SET NULL", use_alter=True),
            nullable=True,
        )


class SoftDeleteMixin:
    """Exclusão lógica (LGPD-friendly): nunca apagamos fisicamente um registro
    de negócio; marcamos `deleted_at` e, quando solicitado, `anonymized_at`
    após anonimizar os dados pessoais."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    anonymized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_anonymized(self) -> bool:
        return self.anonymized_at is not None
