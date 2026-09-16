from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin
from app.models.enums import TipoVeiculoEnum

if TYPE_CHECKING:
    from app.models.unidade import Unidade


class Veiculo(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "veiculos"

    id: Mapped[int] = mapped_column(primary_key=True)
    unidade_id: Mapped[int] = mapped_column(ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False)
    placa: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    modelo: Mapped[str] = mapped_column(String(100), nullable=False)
    cor: Mapped[str] = mapped_column(String(40), nullable=False)
    tipo: Mapped[TipoVeiculoEnum] = mapped_column(
        SAEnum(
            TipoVeiculoEnum,
            name="tipo_veiculo_enum",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=TipoVeiculoEnum.CARRO,
    )

    unidade: Mapped["Unidade"] = relationship("Unidade", back_populates="veiculos")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Veiculo id={self.id} placa={self.placa!r}>"
