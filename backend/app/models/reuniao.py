from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin
from app.models.enums import StatusReuniaoEnum, TipoReuniaoEnum

if TYPE_CHECKING:
    from app.models.predio import Predio
    from app.models.reuniao_presenca import ReuniaoPresenca


class Reuniao(Base, TimestampMixin, AuditMixin):
    """Convocação de reunião/assembleia (ordinária ou extraordinária) - só
    síndico/administrador convoca, mas é visível a QUALQUER papel do
    prédio (a convocação em si é pública por natureza, aparece inclusive
    na tela inicial - ver GET /reunioes).

    `pauta` é texto livre (um item por linha) - lista estruturada teria
    exigido uma tabela à parte para um ganho que a Fase 3 não pediu.
    `ata` só existe depois que a reunião acontece (`registrar_ata`), o que
    também fecha o ciclo de vida (`status` vai para REALIZADA).
    """

    __tablename__ = "reunioes"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[TipoReuniaoEnum] = mapped_column(
        SAEnum(
            TipoReuniaoEnum,
            name="tipo_reuniao_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    status: Mapped[StatusReuniaoEnum] = mapped_column(
        SAEnum(
            StatusReuniaoEnum,
            name="status_reuniao_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=StatusReuniaoEnum.CONVOCADA,
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    local: Mapped[str] = mapped_column(String(255), nullable=False)
    pauta: Mapped[str] = mapped_column(Text, nullable=False)
    ata: Mapped[str | None] = mapped_column(Text, nullable=True)
    ata_registrada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ata_registrada_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )

    predio: Mapped["Predio"] = relationship("Predio")
    presencas: Mapped[list["ReuniaoPresenca"]] = relationship(
        "ReuniaoPresenca", back_populates="reuniao", order_by="ReuniaoPresenca.created_at"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Reuniao id={self.id} titulo={self.titulo!r} status={self.status}>"
