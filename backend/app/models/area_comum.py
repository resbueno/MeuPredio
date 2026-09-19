from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.predio import Predio
    from app.models.reserva import Reserva


class AreaComum(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Um espaço reservável do condomínio (salão de festas, churrasqueira,
    quadra...) - cadastrado só por síndico/administrador (ver
    routers/areas_comuns.py).

    `agenda_liberada_ate` é a fronteira da janela de reservas: qualquer data
    entre hoje e essa data (inclusive) pode ser reservada; `None` significa
    "agenda fechada, nenhuma data liberada ainda". A gestão empurra essa
    data para frente periodicamente (ex.: "liberar os próximos 60 dias") em
    vez de o morador poder reservar um ano à frente sem controle.
    """

    __tablename__ = "areas_comuns"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    capacidade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    agenda_liberada_ate: Mapped[date | None] = mapped_column(Date, nullable=True)

    predio: Mapped["Predio"] = relationship("Predio")
    reservas: Mapped[list["Reserva"]] = relationship("Reserva", back_populates="area_comum")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AreaComum id={self.id} predio_id={self.predio_id} nome={self.nome!r}>"
