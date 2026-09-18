from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.associations import usuario_unidades
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin
from app.models.enums import RoleEnum

if TYPE_CHECKING:
    from app.models.predio import Predio
    from app.models.unidade import Unidade
    from app.models.usuario_papel_extra import UsuarioPapelExtra


class Usuario(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Multi-tenant: todo usuário pertence a um único `Predio` (isolamento
    forte entre condomínios), EXCETO o `ADMINISTRADOR` (papel global da
    plataforma, sem prédio - por isso `predio_id` é nullable). A
    `CheckConstraint` abaixo é a fonte de verdade desse invariante a nível de
    banco: `administrador` <=> `predio_id IS NULL`, nas duas direções.

    O vínculo com unidade(s) é N:N (`usuario_unidades`) - uma pessoa pode ser
    proprietária/moradora de mais de uma unidade do mesmo prédio. Exigir
    "pelo menos uma unidade" para papéis não-administrador é uma regra de
    aplicação (ver routers/schemas), não expressável como constraint de
    banco numa relação N:N sem trigger dedicado.
    """

    __tablename__ = "usuarios"
    __table_args__ = (
        # E-mail é único DENTRO do prédio (dois prédios são inquilinos
        # isolados; nada impede a mesma pessoa/e-mail de logar em prédios
        # diferentes) e único globalmente entre administradores (que não têm
        # prédio). Dois índices parciais em vez de um UniqueConstraint comum
        # porque Postgres trata cada NULL de `predio_id` como distinto entre
        # si - um UniqueConstraint(predio_id, email) simples NÃO impediria
        # dois administradores com o mesmo e-mail.
        Index(
            "uq_usuarios_email_por_predio",
            "predio_id",
            "email",
            unique=True,
            postgresql_where=text("predio_id IS NOT NULL"),
        ),
        Index(
            "uq_usuarios_email_administrador",
            "email",
            unique=True,
            postgresql_where=text("predio_id IS NULL"),
        ),
        CheckConstraint(
            "(role = 'administrador' AND predio_id IS NULL) "
            "OR (role <> 'administrador' AND predio_id IS NOT NULL)",
            name="ck_usuarios_administrador_sem_predio",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(RoleEnum, name="role_enum", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=RoleEnum.MORADOR,
    )
    predio_id: Mapped[int | None] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    consent_lgpd_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    predio: Mapped["Predio | None"] = relationship(
        "Predio", back_populates="usuarios", foreign_keys=[predio_id]
    )
    unidades: Mapped[list["Unidade"]] = relationship(
        "Unidade", secondary=usuario_unidades, back_populates="usuarios"
    )
    papeis_extra: Mapped[list["UsuarioPapelExtra"]] = relationship(
        "UsuarioPapelExtra",
        back_populates="usuario",
        foreign_keys="UsuarioPapelExtra.usuario_id",
        cascade="all, delete-orphan",
    )

    @property
    def roles_efetivos(self) -> set[RoleEnum]:
        """Papel principal + papéis adicionais (ver `UsuarioPapelExtra`) -
        conjunto usado por toda checagem de permissão que hoje faria
        `current_user.role in (...)`. `ADMINISTRADOR` nunca aparece como
        extra (exclusivo, ver validação em routers/usuarios.py), então
        checagens que dependem de "é EXATAMENTE o administrador global"
        continuam usando `.role` direto, não este conjunto."""
        return {self.role} | {p.role for p in self.papeis_extra}

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Usuario id={self.id} email={self.email!r} role={self.role} predio_id={self.predio_id}>"
