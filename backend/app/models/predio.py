from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.predio_convite import PredioConvite
    from app.models.unidade import Unidade
    from app.models.usuario import Usuario


class Predio(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Um condomínio/prédio: a raiz do isolamento multi-tenant do sistema.

    `cep` + `numero` (numeração do endereço, não confundir com número de
    unidade/apartamento) são exatamente o par que o usuário digita na
    primeira etapa do login para identificar em qual prédio está entrando -
    por isso a unicidade é sobre esse par, não sobre `cep` sozinho (dois
    prédios podem estar no mesmo CEP, números de rua diferentes).

    `logradouro`/`bairro`/`cidade`/`uf` são preenchidos automaticamente via
    consulta ao ViaCEP no momento do cadastro (ver `app/core/viacep.py`) -
    guardados aqui (não recalculados a cada leitura) para o sistema
    continuar funcionando mesmo se o ViaCEP ficar indisponível depois.
    """

    __tablename__ = "predios"
    __table_args__ = (UniqueConstraint("cep", "numero", name="uq_predios_cep_numero"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cep: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    complemento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logradouro: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bairro: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cidade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    # Chave de API do Groq deste prédio (OCR de boletos, Fase 2), cifrada
    # em repouso via app/core/crypto.py - nunca fica em texto plano no banco
    # nem é devolvida em nenhuma resposta da API (ver PredioIntegracaoOcrStatus).
    groq_api_key_cifrada: Mapped[str | None] = mapped_column(String(500), nullable=True)

    unidades: Mapped[list["Unidade"]] = relationship("Unidade", back_populates="predio")
    usuarios: Mapped[list["Usuario"]] = relationship(
        "Usuario", back_populates="predio", foreign_keys="Usuario.predio_id"
    )
    convites: Mapped[list["PredioConvite"]] = relationship(
        "PredioConvite", back_populates="predio"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Predio id={self.id} nome={self.nome!r} cep={self.cep!r} numero={self.numero!r}>"
