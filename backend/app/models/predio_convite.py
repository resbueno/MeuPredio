from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.predio import Predio


class PredioConvite(Base, TimestampMixin, AuditMixin):
    """Link de autocadastro de um prédio: um token único e reutilizável que o
    síndico/administrador distribui aos moradores/proprietários para que
    cada um crie sua própria conta (escolhendo sua(s) própria(s) unidade(s)
    dentre as do prédio) sem precisar de cadastro manual um a um.

    Sem soft-delete próprio: revogar é `ativo=False` (o convite nunca
    precisa de auditoria de "quem apagou", só de "quem desativou", já
    coberto pelo log de auditoria da ação no router).
    """

    __tablename__ = "predio_convites"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expira_em: Mapped[date | None] = mapped_column(Date, nullable=True)

    predio: Mapped["Predio"] = relationship("Predio", back_populates="convites")

    @property
    def esta_valido(self) -> bool:
        if not self.ativo:
            return False
        if self.expira_em is None:
            return True
        return self.expira_em >= datetime.now(timezone.utc).date()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PredioConvite id={self.id} predio_id={self.predio_id} ativo={self.ativo}>"
