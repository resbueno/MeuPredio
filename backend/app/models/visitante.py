from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, TimestampMixin
from app.models.enums import TipoDocumentoVisitanteEnum

if TYPE_CHECKING:
    from app.models.predio import Predio
    from app.models.unidade import Unidade


class Visitante(Base, TimestampMixin, AuditMixin):
    """Registro de entrada de um visitante na portaria - livro de log,
    append-only (sem edição/exclusão, mesmo espírito de `LogAuditoria`).
    Visível só à gestão operacional do prédio (zelador/síndico/administrador,
    ver routers/visitantes.py) - não ao morador, que não tem motivo para
    consultar o livro de visitantes de outras unidades.
    """

    __tablename__ = "visitantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    unidade_id: Mapped[int] = mapped_column(
        ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nome_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_documento: Mapped[TipoDocumentoVisitanteEnum] = mapped_column(
        SAEnum(
            TipoDocumentoVisitanteEnum,
            name="tipo_documento_visitante_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    # Preenchido em todo tipo, exceto NAO_INFORMADO (ver validação no schema).
    numero_documento: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Dados do veículo do visitante - todos opcionais (nem todo visitante
    # chega de carro), sem vínculo com o cadastro de Veiculo do morador
    # (mesmo espírito de "log", não de cadastro permanente).
    veiculo_placa: Mapped[str | None] = mapped_column(String(10), nullable=True)
    veiculo_modelo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    veiculo_cor: Mapped[str | None] = mapped_column(String(40), nullable=True)

    predio: Mapped["Predio"] = relationship("Predio")
    unidade: Mapped["Unidade"] = relationship("Unidade")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Visitante id={self.id} unidade_id={self.unidade_id} nome={self.nome_completo!r}>"
