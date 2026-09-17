"""fornecedores e despesas_lancamentos (Fase 2 - fundacao do motor financeiro)

Revision ID: 0003_fornecedores_despesas
Revises: 0002_audit_immutability_trigger
Create Date: 2026-09-17

Primeira fatia da Fase 2 (Motor Financeiro): apenas o cadastro de
fornecedores e o CRUD de lancamentos de despesa. Rateio entre unidades, OCR
de boletos (Mistral AI) e remessa/retorno bancario ficam para migrations
futuras.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_fornecedores_despesas"
down_revision: Union[str, None] = "0002_audit_immutability_trigger"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

status_despesa_enum = postgresql.ENUM(
    "pendente", "pago", "cancelado", name="status_despesa_enum"
)


def upgrade() -> None:
    # --- fornecedores ---
    op.create_table(
        "fornecedores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("documento", sa.String(20), nullable=True),
        sa.Column("categoria", sa.String(100), nullable=False),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_fornecedores_created_by"),
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
        sa.UniqueConstraint("documento", name="uq_fornecedores_documento"),
    )
    op.create_index("ix_fornecedores_categoria", "fornecedores", ["categoria"])

    # --- despesas_lancamentos ---
    # NAO criar status_despesa_enum manualmente aqui: o SQLAlchemy ja cria o
    # tipo automaticamente via create_table (mesma licao da migration 0001 -
    # criar o ENUM antes causa DuplicateObject contra um Postgres real).
    op.create_table(
        "despesas_lancamentos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fornecedor_id",
            sa.Integer(),
            sa.ForeignKey(
                "fornecedores.id", ondelete="SET NULL", name="fk_despesas_lancamentos_fornecedor_id"
            ),
            nullable=True,
        ),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("categoria", sa.String(100), nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        sa.Column(
            "status",
            status_despesa_enum,
            nullable=False,
            server_default=sa.text("'pendente'::status_despesa_enum"),
        ),
        sa.Column("documento_url", sa.String(500), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_despesas_lancamentos_created_by"
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
    )
    op.create_index(
        "ix_despesas_lancamentos_categoria", "despesas_lancamentos", ["categoria"]
    )
    op.create_index(
        "ix_despesas_lancamentos_data_vencimento", "despesas_lancamentos", ["data_vencimento"]
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_despesas_lancamentos_data_vencimento", table_name="despesas_lancamentos")
    op.drop_index("ix_despesas_lancamentos_categoria", table_name="despesas_lancamentos")
    op.drop_table("despesas_lancamentos")
    status_despesa_enum.drop(bind, checkfirst=True)

    op.drop_index("ix_fornecedores_categoria", table_name="fornecedores")
    op.drop_table("fornecedores")
