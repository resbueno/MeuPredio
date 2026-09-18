from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.reuniao import Reuniao
    from app.models.unidade import Unidade


class ReuniaoPresenca(Base, TimestampMixin, AuditMixin):
    """Presença é por UNIDADE, não por pessoa - quórum de assembleia de
    condomínio se conta por unidade representada, não por número de
    moradores presentes. `created_by` (via AuditMixin) é quem registrou
    (o próprio morador confirmando a própria unidade, ou a gestão
    registrando por alguém na entrada)."""

    __tablename__ = "reunioes_presencas"
    __table_args__ = (
        UniqueConstraint("reuniao_id", "unidade_id", name="uq_reunioes_presencas_reuniao_unidade"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reuniao_id: Mapped[int] = mapped_column(
        ForeignKey("reunioes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reuniao: Mapped["Reuniao"] = relationship("Reuniao", back_populates="presencas")
    unidade: Mapped["Unidade"] = relationship("Unidade")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ReuniaoPresenca reuniao_id={self.reuniao_id} unidade_id={self.unidade_id}>"
