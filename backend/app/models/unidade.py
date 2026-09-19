from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.associations import usuario_unidades
from app.models.base import AuditMixin, SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.predio import Predio
    from app.models.usuario import Usuario
    from app.models.veiculo import Veiculo


class Unidade(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    """Uma unidade (bloco+número) pertence a exatamente um `Predio`.

    A propriedade/moradia (quem é "dono" ou "morador" desta unidade) não é
    mais um campo aqui (ver histórico: `proprietario_id` existia na Fase 1) -
    é modelada do lado de `Usuario`, via a relação N:N `usuario_unidades` +
    o papel (`role`) de cada usuário vinculado. Isso permite naturalmente
    mais de um proprietário/morador por unidade, e uma pessoa com mais de
    uma unidade, sem duas fontes de verdade sobre "quem mora/é dono de onde".
    """

    __tablename__ = "unidades"
    __table_args__ = (
        UniqueConstraint("predio_id", "bloco", "numero", name="uq_unidades_predio_bloco_numero"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    predio_id: Mapped[int] = mapped_column(
        ForeignKey("predios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bloco: Mapped[str] = mapped_column(String(20), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    # Peso usado pelo motor de rateio (ver despesas/ratear) quando o critério
    # é "fracao_ideal" - não precisa somar 100 entre as unidades do prédio
    # (o cálculo usa a fração de CADA unidade sobre a SOMA das frações
    # ativas), mas na prática costuma refletir a fração ideal do condomínio.
    # Nullable: nem toda unidade tem esse dado definido ainda.
    fracao_ideal: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    # Identificação da vaga de garagem vinculada - texto livre (nem todo
    # condomínio numera vagas de forma simples, ex.: "12A", "Subsolo 2 - 34")
    # e opcional (nem toda unidade tem vaga própria).
    vaga: Mapped[str | None] = mapped_column(String(20), nullable=True)

    predio: Mapped["Predio"] = relationship("Predio", back_populates="unidades")
    usuarios: Mapped[list["Usuario"]] = relationship(
        "Usuario", secondary=usuario_unidades, back_populates="unidades"
    )
    veiculos: Mapped[list["Veiculo"]] = relationship("Veiculo", back_populates="unidade")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Unidade id={self.id} predio_id={self.predio_id} bloco={self.bloco!r} numero={self.numero!r}>"
