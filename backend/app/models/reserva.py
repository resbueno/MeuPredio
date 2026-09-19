from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Index, Text, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin
from app.models.enums import StatusReservaEnum

if TYPE_CHECKING:
    from app.models.area_comum import AreaComum
    from app.models.predio import Predio
    from app.models.unidade import Unidade


class Reserva(Base, TimestampMixin, AuditMixin):
    """Reserva de uma `AreaComum` por uma unidade, para UM dia inteiro (sem
    horário/turno - simplificação deliberada: um evento por área por dia).

    O índice parcial único (area_comum_id, data) WHERE status='confirmada'
    é a fonte de verdade contra dupla reserva - impede duas reservas
    confirmadas na mesma área+data mesmo sob concorrência, sem impedir uma
    nova reserva depois que a antiga foi cancelada (cancelada não conta).
    """

    __tablename__ = "reservas"
    __table_args__ = (
        Index(
            "uq_reservas_area_data_confirmada",
            "area_comum_id",
            "data",
            unique=True,
            postgresql_where=text("status = 'confirmada'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    area_comum_id: Mapped[int] = mapped_column(
        ForeignKey("areas_comuns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[StatusReservaEnum] = mapped_column(
        SAEnum(
            StatusReservaEnum,
            name="status_reserva_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=StatusReservaEnum.CONFIRMADA,
    )
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelada_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )

    predio: Mapped["Predio"] = relationship("Predio")
    area_comum: Mapped["AreaComum"] = relationship("AreaComum", back_populates="reservas")
    unidade: Mapped["Unidade"] = relationship("Unidade")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Reserva id={self.id} area_comum_id={self.area_comum_id} data={self.data} status={self.status}>"
