"""numero da vaga de garagem na unidade

Revision ID: 0017_unidades_vaga
Revises: 0016_visitantes_veiculo
Create Date: 2026-09-20
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0017_unidades_vaga"
down_revision: Union[str, None] = "0016_visitantes_veiculo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("unidades", sa.Column("vaga", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("unidades", "vaga")
