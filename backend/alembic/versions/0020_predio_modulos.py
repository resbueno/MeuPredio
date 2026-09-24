"""modulos habilitados por predio

Revision ID: 0020_predio_modulos
Revises: 0019_equipe_prestadores
Create Date: 2026-09-24
"""
from __future__ import annotations

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0020_predio_modulos"
down_revision: Union[str, None] = "0019_equipe_prestadores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TODOS_MODULOS = [
    "veiculos",
    "financeiro",
    "avisos",
    "ocorrencias",
    "chamados",
    "reunioes",
    "entregas",
    "visitantes",
    "reservas",
    "equipe",
]


def upgrade() -> None:
    op.add_column(
        "predios",
        sa.Column(
            "modulos_habilitados",
            JSONB,
            nullable=False,
            server_default=sa.text(f"'{json.dumps(_TODOS_MODULOS)}'::jsonb"),
        ),
    )
    op.alter_column("predios", "modulos_habilitados", server_default=None)


def downgrade() -> None:
    op.drop_column("predios", "modulos_habilitados")
