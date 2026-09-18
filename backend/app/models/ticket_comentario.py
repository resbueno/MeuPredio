from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.ticket_atendimento import TicketAtendimento


class TicketComentario(Base, TimestampMixin, AuditMixin):
    """Uma mensagem na conversa de um chamado - `created_by` (de
    `AuditMixin`) e o autor. Sem edicao/exclusao (mesmo espirito de
    `RateioDespesaItem`: um comentario e um fato imutavel do historico do
    chamado)."""

    __tablename__ = "tickets_comentarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets_atendimento.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)

    ticket: Mapped["TicketAtendimento"] = relationship(
        "TicketAtendimento", back_populates="comentarios"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TicketComentario id={self.id} ticket_id={self.ticket_id}>"
