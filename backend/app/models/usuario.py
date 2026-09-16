from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin
from app.models.enums import RoleEnum

if TYPE_CHECKING:
    from app.models.unidade import Unidade


class Usuario(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(RoleEnum, name="role_enum", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=RoleEnum.MORADOR,
    )
    # FK opcional: a qual unidade este usuário está vinculado (ex.: morador).
    # `use_alter=True` porque `unidades.proprietario_id` referencia de volta
    # `usuarios.id` — quebra o ciclo de criação das tabelas (ver migration
    # inicial, que cria esta constraint via ALTER TABLE após ambas existirem).
    unidade_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidades.id", ondelete="SET NULL", use_alter=True, name="fk_usuarios_unidade_id"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    consent_lgpd_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    unidade: Mapped["Unidade | None"] = relationship(
        "Unidade", foreign_keys=[unidade_id], back_populates="moradores"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Usuario id={self.id} email={self.email!r} role={self.role}>"
