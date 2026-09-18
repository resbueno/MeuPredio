from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import TipoNotificacaoEnum

if TYPE_CHECKING:
    from app.models.predio import Predio
    from app.models.usuario import Usuario


class Notificacao(Base, TimestampMixin):
    """Uma entrada do sino de alertas, sempre endereçada a UM usuário
    específico - "fan-out" na criação: um aviso de condomínio para 50
    moradores vira 50 linhas aqui, uma por destinatário, cada uma com seu
    próprio `lida_em`. Gerada por app/core/notificacoes.py a partir de
    outros módulos (avisos, ocorrências, reuniões, entregas) - nunca criada
    diretamente pelo cliente, por isso não tem router de escrita além de
    marcar como lida.

    `referencia_tipo`/`referencia_id` apontam para o registro de origem
    (ex.: "aviso_direto"/42) só para eventual link/deep-link futuro - não é
    FK porque a origem varia por tipo de notificação."""

    __tablename__ = "notificacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[TipoNotificacaoEnum] = mapped_column(
        SAEnum(
            TipoNotificacaoEnum,
            name="tipo_notificacao_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    referencia_tipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    referencia_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    predio: Mapped["Predio"] = relationship("Predio")
    usuario: Mapped["Usuario"] = relationship("Usuario")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Notificacao id={self.id} usuario_id={self.usuario_id} tipo={self.tipo}>"
