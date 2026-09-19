from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class ContatoLead(Base, TimestampMixin):
    """Pedido de contato enviado pela landing page institucional (fora de
    qualquer prédio/tenant - é sobre o produto MeuPrédio em si, não sobre um
    condomínio específico). Sem infraestrutura de e-mail no projeto ainda,
    então o "envio" é só persistir aqui; o administrador consulta a lista
    (GET /contato) para dar retorno manualmente."""

    __tablename__ = "contatos_lead"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)
    atendido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ContatoLead id={self.id} email={self.email!r}>"
