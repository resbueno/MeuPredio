from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin
from app.models.enums import RoleEnum

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class UsuarioPapelExtra(Base, TimestampMixin, AuditMixin):
    """Papel ADICIONAL de um usuário, além do `Usuario.role` principal - ex.:
    um síndico que também é morador da própria unidade. `ADMINISTRADOR`
    nunca aparece aqui (papel global exclusivo, ver validação em
    routers/usuarios.py); um mesmo papel não se repete para o mesmo usuário
    (`UniqueConstraint`), e reaparecer como papel principal depois não deixa
    duplicidade (o router remove a entrada extra correspondente nesse caso).
    """

    __tablename__ = "usuarios_papeis_extras"
    __table_args__ = (
        UniqueConstraint("usuario_id", "role", name="uq_usuarios_papeis_extras_usuario_role"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[RoleEnum] = mapped_column(
        SAEnum(
            RoleEnum,
            name="role_enum",
            native_enum=True,
            create_type=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )

    usuario: Mapped["Usuario"] = relationship(
        "Usuario", back_populates="papeis_extra", foreign_keys=[usuario_id]
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<UsuarioPapelExtra usuario_id={self.usuario_id} role={self.role}>"
