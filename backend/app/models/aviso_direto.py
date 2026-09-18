from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin
from app.models.enums import DestinatarioAvisoEnum, TipoAvisoDiretoEnum

if TYPE_CHECKING:
    from app.models.despesa_lancamento import DespesaLancamento
    from app.models.predio import Predio
    from app.models.unidade import Unidade


class AvisoDireto(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Aviso/advertência/multa dirigido a UMA unidade específica - só
    síndico/administrador emite (ver routers/avisos_diretos.py). Visível
    apenas a quem está vinculado à `unidade_id` E bate com `destinatario`
    (morador, proprietário ou ambos).

    Conversa de resposta única, não uma thread: o destinatário responde
    UMA vez (`resposta`/`respondido_por`/`respondido_em`) e isso encerra -
    quem só quer confirmar leitura usa `lida_em` sem preencher `resposta`.
    Um novo assunto é um aviso novo, nunca uma resposta à resposta.
    """

    __tablename__ = "avisos_diretos"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    destinatario: Mapped[DestinatarioAvisoEnum] = mapped_column(
        SAEnum(
            DestinatarioAvisoEnum,
            name="destinatario_aviso_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    tipo: Mapped[TipoAvisoDiretoEnum] = mapped_column(
        SAEnum(
            TipoAvisoDiretoEnum,
            name="tipo_aviso_direto_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        index=True,
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    # Só preenchido quando tipo == MULTA - o valor cobrado, espelhado na
    # despesa vinculada (ver `despesa_lancamento_id`) como fonte de verdade
    # financeira; este campo é só o registro do aviso em si.
    valor: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    despesa_lancamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("despesas_lancamentos.id", ondelete="SET NULL"), nullable=True
    )

    lida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resposta: Mapped[str | None] = mapped_column(Text, nullable=True)
    respondido_por: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    respondido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    predio: Mapped["Predio"] = relationship("Predio")
    unidade: Mapped["Unidade"] = relationship("Unidade")
    despesa_lancamento: Mapped["DespesaLancamento | None"] = relationship("DespesaLancamento")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AvisoDireto id={self.id} unidade_id={self.unidade_id} tipo={self.tipo}>"
