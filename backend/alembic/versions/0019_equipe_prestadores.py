"""funcionarios e prestadores de servico (custo rateavel)

Revision ID: 0019_equipe_prestadores
Revises: 0018_contato_lead
Create Date: 2026-09-21
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019_equipe_prestadores"
down_revision: Union[str, None] = "0018_contato_lead"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_cols(prefixo: str) -> list[sa.Column]:
    return [
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name=f"fk_{prefixo}_created_by"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anonymized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "funcionarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_funcionarios_predio_id"),
            nullable=False,
        ),
        sa.Column("nome_completo", sa.String(255), nullable=False),
        sa.Column("cargo", sa.String(100), nullable=False),
        sa.Column("cpf", sa.String(11), nullable=True),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("data_admissao", sa.Date(), nullable=True),
        sa.Column("salario", sa.Numeric(12, 2), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("observacoes", sa.Text(), nullable=True),
        *_audit_cols("funcionarios"),
    )
    op.create_index("ix_funcionarios_predio_id", "funcionarios", ["predio_id"])

    op.create_table(
        "prestadores_servico",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_prestadores_servico_predio_id"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("tipo_servico", sa.String(100), nullable=False),
        sa.Column("razao_social", sa.String(255), nullable=True),
        sa.Column("cnpj", sa.String(14), nullable=True),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("custo_mensal", sa.Numeric(12, 2), nullable=False),
        sa.Column("incluir_no_rateio", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("criterio_rateio", sa.String(20), nullable=False, server_default="igual"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("observacoes", sa.Text(), nullable=True),
        *_audit_cols("prestadores_servico"),
    )
    op.create_index("ix_prestadores_servico_predio_id", "prestadores_servico", ["predio_id"])

    op.add_column("despesas_lancamentos", sa.Column("prestador_servico_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_despesas_lancamentos_prestador_servico_id",
        "despesas_lancamentos",
        "prestadores_servico",
        ["prestador_servico_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_despesas_lancamentos_prestador_servico_id", "despesas_lancamentos", ["prestador_servico_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_despesas_lancamentos_prestador_servico_id", table_name="despesas_lancamentos")
    op.drop_constraint(
        "fk_despesas_lancamentos_prestador_servico_id", "despesas_lancamentos", type_="foreignkey"
    )
    op.drop_column("despesas_lancamentos", "prestador_servico_id")
    op.drop_index("ix_prestadores_servico_predio_id", table_name="prestadores_servico")
    op.drop_table("prestadores_servico")
    op.drop_index("ix_funcionarios_predio_id", table_name="funcionarios")
    op.drop_table("funcionarios")
