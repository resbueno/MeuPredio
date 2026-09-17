from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.despesa_lancamento import DespesaLancamento


class Fornecedor(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Diretório de fornecedores/prestadores de serviço (Fase 2 - Motor
    Financeiro). `documento` (CPF ou CNPJ) é opcional na criação porque nem
    todo fornecedor cadastrado às pressas para lançar uma despesa tem esse
    dado em mãos — mas quando informado, deve ser único."""

    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    documento: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    categoria: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    despesas: Mapped[list["DespesaLancamento"]] = relationship(
        "DespesaLancamento", back_populates="fornecedor"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Fornecedor id={self.id} nome={self.nome!r}>"
