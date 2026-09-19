"""pedidos de contato da landing page

Revision ID: 0018_contato_lead
Revises: 0017_unidades_vaga
Create Date: 2026-09-20
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0018_contato_lead"
down_revision: Union[str, None] = "0017_unidades_vaga"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contatos_lead",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("telefone", sa.String(20), nullable=True),
        sa.Column("mensagem", sa.Text(), nullable=True),
        sa.Column("atendido", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_contatos_lead_email", "contatos_lead", ["email"])


def downgrade() -> None:
    op.drop_index("ix_contatos_lead_email", table_name="contatos_lead")
    op.drop_table("contatos_lead")
