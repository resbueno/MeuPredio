from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LogAuditoria(Base):
    """Trilha de auditoria. Somente INSERT: um trigger de banco (ver migration
    `xxxx_audit_immutability_trigger`) bloqueia UPDATE e DELETE nesta tabela
    em nível de banco de dados — nenhuma camada de aplicação pode contornar
    essa proteção. Por isso este modelo não usa TimestampMixin (que inclui
    `updated_at`, sem sentido aqui) nem SoftDeleteMixin.
    """

    __tablename__ = "logs_auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    acao: Mapped[str] = mapped_column(String(50), nullable=False)
    entidade: Mapped[str] = mapped_column(String(100), nullable=False)
    entidade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dados_antes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dados_depois: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_origem: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LogAuditoria id={self.id} acao={self.acao!r} entidade={self.entidade!r}>"
