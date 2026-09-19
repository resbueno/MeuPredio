"""contas recorrentes e dados societarios do fornecedor (cnpj/razao social/nome fantasia)

Revision ID: 0015_despesas_recorrentes
Revises: 0014_visitantes_reservas
Create Date: 2026-09-19

DespesaRecorrente: modelo de conta que se repete todo mes (agua, luz,
contrato de zeladoria...), gerando DespesaLancamento automaticamente (ver
app/core/despesas_recorrentes.py). despesas_lancamentos ganha
despesa_recorrente_id (rastreabilidade, nullable) e fornecedores ganha
cnpj/razao_social/nome_fantasia (identificacao societaria completa da
empresa por tras da conta).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0015_despesas_recorrentes"
down_revision: Union[str, None] = "0014_visitantes_reservas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("fornecedores", sa.Column("cnpj", sa.String(18), nullable=True))
    op.add_column("fornecedores", sa.Column("razao_social", sa.String(255), nullable=True))
    op.add_column("fornecedores", sa.Column("nome_fantasia", sa.String(255), nullable=True))

    op.create_table(
        "despesas_recorrentes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_despesas_recorrentes_predio_id"),
            nullable=False,
        ),
        sa.Column(
            "fornecedor_id",
            sa.Integer(),
            sa.ForeignKey(
                "fornecedores.id", ondelete="SET NULL", name="fk_despesas_recorrentes_fornecedor_id"
            ),
            nullable=True,
        ),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey(
                "unidades.id", ondelete="SET NULL", name="fk_despesas_recorrentes_unidade_id"
            ),
            nullable=True,
        ),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("categoria", sa.String(100), nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("dia_vencimento", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=True),
        sa.Column("ultima_geracao", sa.Date(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_despesas_recorrentes_created_by"
            ),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("dia_vencimento >= 1 AND dia_vencimento <= 28", name="ck_despesas_recorrentes_dia_vencimento"),
    )
    op.create_index("ix_despesas_recorrentes_predio_id", "despesas_recorrentes", ["predio_id"])
    op.create_index("ix_despesas_recorrentes_categoria", "despesas_recorrentes", ["categoria"])

    op.add_column(
        "despesas_lancamentos", sa.Column("despesa_recorrente_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_despesas_lancamentos_despesa_recorrente_id",
        "despesas_lancamentos",
        "despesas_recorrentes",
        ["despesa_recorrente_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_despesas_lancamentos_despesa_recorrente_id", "despesas_lancamentos", type_="foreignkey"
    )
    op.drop_column("despesas_lancamentos", "despesa_recorrente_id")

    op.drop_index("ix_despesas_recorrentes_categoria", table_name="despesas_recorrentes")
    op.drop_index("ix_despesas_recorrentes_predio_id", table_name="despesas_recorrentes")
    op.drop_table("despesas_recorrentes")

    op.drop_column("fornecedores", "nome_fantasia")
    op.drop_column("fornecedores", "razao_social")
    op.drop_column("fornecedores", "cnpj")
