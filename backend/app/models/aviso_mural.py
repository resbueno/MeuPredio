from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin
from app.models.enums import TipoAvisoMuralEnum

if TYPE_CHECKING:
    from app.models.predio import Predio


class AvisoMural(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Um item do mural do prédio - dois blocos possíveis (`tipo`):
    'condominio' (só síndico/administrador, ver RBAC no router) e 'anuncio'
    (classificado, qualquer morador/proprietário publica o próprio; só o
    autor edita, mas a gestão também pode remover - ver `_pode_editar` e
    `_pode_remover` em routers/avisos_mural.py)."""

    __tablename__ = "avisos_mural"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[TipoAvisoMuralEnum] = mapped_column(
        SAEnum(
            TipoAvisoMuralEnum,
            name="tipo_aviso_mural_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    # Só usado em anuncios (classificados) - preço é opcional mesmo ali (nem
    # todo anúncio tem um valor fixo, ex. "troco por...").
    preco: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    predio: Mapped["Predio"] = relationship("Predio")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AvisoMural id={self.id} tipo={self.tipo} titulo={self.titulo!r}>"
