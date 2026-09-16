from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.usuario import Usuario
    from app.models.veiculo import Veiculo


class Unidade(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "unidades"
    __table_args__ = (UniqueConstraint("bloco", "numero", name="uq_unidades_bloco_numero"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    bloco: Mapped[str] = mapped_column(String(20), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    proprietario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )

    proprietario: Mapped["Usuario | None"] = relationship(
        "Usuario", foreign_keys=[proprietario_id]
    )
    moradores: Mapped[list["Usuario"]] = relationship(
        "Usuario", foreign_keys="Usuario.unidade_id", back_populates="unidade"
    )
    veiculos: Mapped[list["Veiculo"]] = relationship("Veiculo", back_populates="unidade")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Unidade id={self.id} bloco={self.bloco!r} numero={self.numero!r}>"
