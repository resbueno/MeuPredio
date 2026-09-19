"""dados de veiculo do visitante

Revision ID: 0016_visitantes_veiculo
Revises: 0015_despesas_recorrentes
Create Date: 2026-09-20

Campos opcionais de veiculo (placa/modelo/cor) no registro de visitante -
nao ha novo endpoint de lote nesta migration (o POST /visitantes/lote
reusa a mesma tabela).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0016_visitantes_veiculo"
down_revision: Union[str, None] = "0015_despesas_recorrentes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("visitantes", sa.Column("veiculo_placa", sa.String(10), nullable=True))
    op.add_column("visitantes", sa.Column("veiculo_modelo", sa.String(100), nullable=True))
    op.add_column("visitantes", sa.Column("veiculo_cor", sa.String(40), nullable=True))


def downgrade() -> None:
    op.drop_column("visitantes", "veiculo_cor")
    op.drop_column("visitantes", "veiculo_modelo")
    op.drop_column("visitantes", "veiculo_placa")
