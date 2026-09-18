from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.predio import Predio
    from app.models.unidade import Unidade
    from app.models.usuario import Usuario


class Entrega(Base, TimestampMixin, AuditMixin):
    """Encomenda/entrega recebida na portaria para UMA unidade - registrada
    por zelador/síndico/administrador (ver routers/entregas.py), nunca pelo
    próprio morador. Gera notificação (ver app/core/notificacoes.py) para
    todos os usuários vinculados à unidade assim que criada.

    `retirada_em`/`retirada_por` fecham o ciclo quando alguém da unidade (ou
    a própria gestão) confirma que já pegou o item - não há edição de
    descrição/localização depois de registrada, só o registro de retirada."""

    __tablename__ = "entregas"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    localizacao: Mapped[str] = mapped_column(String(255), nullable=False)
    retirada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retirada_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )

    predio: Mapped["Predio"] = relationship("Predio")
    unidade: Mapped["Unidade"] = relationship("Unidade")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Entrega id={self.id} unidade_id={self.unidade_id} retirada_em={self.retirada_em}>"
