"""rateio de despesas entre unidades (Fase 2 - motor financeiro)

Revision ID: 0005_rateio_despesas
Revises: 0004_multi_tenant_predios
Create Date: 2026-09-17

Segunda fatia da Fase 2 (Motor Financeiro): calcula e distribui cada
despesa entre as unidades ativas do prédio, por dois critérios ("igual" ou
"fracao_ideal"). OCR de boletos (Mistral AI) e remessa/retorno bancário
continuam fora do escopo desta migration.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_rateio_despesas"
down_revision: Union[str, None] = "0004_multi_tenant_predios"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

criterio_rateio_enum = postgresql.ENUM(
    "igual", "fracao_ideal", name="criterio_rateio_enum"
)


def upgrade() -> None:
    op.add_column("unidades", sa.Column("fracao_ideal", sa.Numeric(9, 6), nullable=True))
    op.add_column(
        "despesas_lancamentos",
        sa.Column("rateado_em", sa.DateTime(timezone=True), nullable=True),
    )

    # NAO criar criterio_rateio_enum manualmente aqui: o SQLAlchemy ja cria o
    # tipo automaticamente via create_table (mesma licao das migrations
    # anteriores - criar o ENUM antes causa DuplicateObject contra um
    # Postgres real).
    op.create_table(
        "rateio_despesa_itens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey(
                "predios.id", ondelete="CASCADE", name="fk_rateio_despesa_itens_predio_id"
            ),
            nullable=False,
        ),
        sa.Column(
            "despesa_lancamento_id",
            sa.Integer(),
            sa.ForeignKey(
                "despesas_lancamentos.id",
                ondelete="CASCADE",
                name="fk_rateio_despesa_itens_despesa_lancamento_id",
            ),
            nullable=False,
        ),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey(
                "unidades.id", ondelete="CASCADE", name="fk_rateio_despesa_itens_unidade_id"
            ),
            nullable=False,
        ),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("criterio", criterio_rateio_enum, nullable=False),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_rateio_despesa_itens_created_by"
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint(
            "despesa_lancamento_id", "unidade_id", name="uq_rateio_despesa_unidade"
        ),
    )
    op.create_index("ix_rateio_despesa_itens_predio_id", "rateio_despesa_itens", ["predio_id"])
    op.create_index(
        "ix_rateio_despesa_itens_despesa_lancamento_id",
        "rateio_despesa_itens",
        ["despesa_lancamento_id"],
    )
    op.create_index("ix_rateio_despesa_itens_unidade_id", "rateio_despesa_itens", ["unidade_id"])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_rateio_despesa_itens_unidade_id", table_name="rateio_despesa_itens")
    op.drop_index(
        "ix_rateio_despesa_itens_despesa_lancamento_id", table_name="rateio_despesa_itens"
    )
    op.drop_index("ix_rateio_despesa_itens_predio_id", table_name="rateio_despesa_itens")
    op.drop_table("rateio_despesa_itens")
    criterio_rateio_enum.drop(bind, checkfirst=True)

    op.drop_column("despesas_lancamentos", "rateado_em")
    op.drop_column("unidades", "fracao_ideal")
