from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.predio import Predio
    from app.models.unidade import Unidade


class Ocorrencia(Base, TimestampMixin, AuditMixin):
    """Livro de ocorrências: qualquer morador/proprietário registra a
    própria; visível a ele e à gestão (síndico/zelador/administrador),
    mesmo padrão de privacidade de `TicketAtendimento`. Só o síndico pode
    editar (ex.: corrigir/complementar o relato), o que acende
    `editado_em`/`editado_por` de forma permanente."""

    __tablename__ = "livro_ocorrencias"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidades.id", ondelete="SET NULL"), nullable=True, index=True
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    editado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    editado_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )

    predio: Mapped["Predio"] = relationship("Predio")
    unidade: Mapped["Unidade | None"] = relationship("Unidade")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Ocorrencia id={self.id} titulo={self.titulo!r}>"
