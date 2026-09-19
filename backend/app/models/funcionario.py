from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.predio import Predio


class Funcionario(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Funcionário do condomínio (porteiro, faxineira, zelador...). Cadastro
    e consulta restritos a síndico/zelador (ver routers/funcionarios.py) -
    contém salário e CPF, por isso nem o morador nem o administrador global
    enxergam. `ativo=False` mantém o histórico de quem já saiu sem apagar."""

    __tablename__ = "funcionarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    cargo: Mapped[str] = mapped_column(String(100), nullable=False)
    cpf: Mapped[str | None] = mapped_column(String(11), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_admissao: Mapped[date | None] = mapped_column(Date, nullable=True)
    salario: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    predio: Mapped["Predio"] = relationship("Predio")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Funcionario id={self.id} nome={self.nome_completo!r}>"
