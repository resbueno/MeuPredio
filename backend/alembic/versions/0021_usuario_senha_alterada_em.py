"""carimbo de troca de senha (revogacao de jwt)

Revision ID: 0021_usuario_senha_alterada_em
Revises: 0020_predio_modulos
Create Date: 2026-09-24
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021_usuario_senha_alterada_em"
down_revision: Union[str, None] = "0020_predio_modulos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column("senha_alterada_em", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("usuarios", "senha_alterada_em")
