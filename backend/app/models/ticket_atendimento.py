from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin
from app.models.enums import CategoriaTicketEnum, PrioridadeTicketEnum, StatusTicketEnum

if TYPE_CHECKING:
    from app.models.predio import Predio
    from app.models.ticket_comentario import TicketComentario
    from app.models.unidade import Unidade


class TicketAtendimento(Base, TimestampMixin, AuditMixin):
    """Chamado de manutencao/duvida/solicitacao (Fase 3 - Portal da
    Transparencia/Comunicacao, ver roadmap). `created_by` (de `AuditMixin`) E
    o autor/morador que abriu o chamado - nao existe campo separado para
    isso, mesmo uso que despesas/fornecedores ja fazem para "quem criou".

    Sem `SoftDeleteMixin` de proposito: um chamado nunca some, ele segue seu
    ciclo de vida ate `resolvido` ou `cancelado` (mesmo padrao de
    `StatusDespesaEnum` em despesas_lancamentos - nunca DELETE, sempre uma
    transicao de status auditavel)."""

    __tablename__ = "tickets_atendimento"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int | None] = mapped_column(
        ForeignKey("unidades.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Quem esta cuidando do chamado (zelador/sindico/administrador) - nulo
    # enquanto ninguem assumiu (`status='aberto'`).
    responsavel_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, index=True
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    categoria: Mapped[CategoriaTicketEnum] = mapped_column(
        SAEnum(
            CategoriaTicketEnum,
            name="categoria_ticket_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    prioridade: Mapped[PrioridadeTicketEnum] = mapped_column(
        SAEnum(
            PrioridadeTicketEnum,
            name="prioridade_ticket_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    status: Mapped[StatusTicketEnum] = mapped_column(
        SAEnum(
            StatusTicketEnum,
            name="status_ticket_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=StatusTicketEnum.ABERTO,
    )
    # Calculado uma vez, na abertura (ver app/core/tickets.py) - nunca
    # recalculado depois, para o prazo nao "andar" se a prioridade mudar.
    prazo_sla: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    predio: Mapped["Predio"] = relationship("Predio")
    unidade: Mapped["Unidade | None"] = relationship("Unidade")
    comentarios: Mapped[list["TicketComentario"]] = relationship(
        "TicketComentario", back_populates="ticket", order_by="TicketComentario.created_at"
    )

    @property
    def esta_atrasado(self) -> bool:
        """Derivado, nunca persistido (mesma logica de `esta_atrasada` em
        DespesaLancamento): so importa enquanto o chamado ainda esta aberto
        ou em andamento."""
        if self.status not in (StatusTicketEnum.ABERTO, StatusTicketEnum.EM_ANDAMENTO):
            return False
        return datetime.now(timezone.utc) > self.prazo_sla

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TicketAtendimento id={self.id} titulo={self.titulo!r} status={self.status}>"
