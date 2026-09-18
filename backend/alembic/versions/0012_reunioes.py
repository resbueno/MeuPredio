"""modulo de reunioes: convocacao, pauta, presenca e ata

Revision ID: 0012_reunioes
Revises: 0011_usuarios_papeis_extras
Create Date: 2026-09-21

Reuniao (convocacao/pauta/ata) + ReuniaoPresenca (presenca por UNIDADE,
nao por pessoa - quorum de assembleia se conta por unidade representada).
Ja nasce com predio_id NOT NULL (sem backfill, tabela nova).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0012_reunioes"
down_revision: Union[str, None] = "0011_usuarios_papeis_extras"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tipo_reuniao_enum = postgresql.ENUM("ordinaria", "extraordinaria", name="tipo_reuniao_enum")
status_reuniao_enum = postgresql.ENUM(
    "convocada", "realizada", "cancelada", name="status_reuniao_enum"
)


def upgrade() -> None:
    # NAO criar os ENUMs manualmente aqui: o SQLAlchemy ja cria os tipos
    # automaticamente via create_table (mesma licao das migrations
    # anteriores - criar o ENUM antes causa DuplicateObject contra um
    # Postgres real).
    op.create_table(
        "reunioes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_reunioes_predio_id"),
            nullable=False,
        ),
        sa.Column("tipo", tipo_reuniao_enum, nullable=False),
        sa.Column(
            "status",
            status_reuniao_enum,
            nullable=False,
            server_default=sa.text("'convocada'::status_reuniao_enum"),
        ),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("data_hora", sa.DateTime(timezone=True), nullable=False),
        sa.Column("local", sa.String(255), nullable=False),
        sa.Column("pauta", sa.Text(), nullable=False),
        sa.Column("ata", sa.Text(), nullable=True),
        sa.Column("ata_registrada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "ata_registrada_por",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_reunioes_ata_registrada_por"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_reunioes_created_by"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_reunioes_predio_id", "reunioes", ["predio_id"])
    op.create_index("ix_reunioes_data_hora", "reunioes", ["data_hora"])

    op.create_table(
        "reunioes_presencas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "reuniao_id",
            sa.Integer(),
            sa.ForeignKey(
                "reunioes.id", ondelete="CASCADE", name="fk_reunioes_presencas_reuniao_id"
            ),
            nullable=False,
        ),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey(
                "unidades.id", ondelete="CASCADE", name="fk_reunioes_presencas_unidade_id"
            ),
            nullable=False,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_reunioes_presencas_created_by"
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
            "reuniao_id", "unidade_id", name="uq_reunioes_presencas_reuniao_unidade"
        ),
    )
    op.create_index("ix_reunioes_presencas_reuniao_id", "reunioes_presencas", ["reuniao_id"])
    op.create_index("ix_reunioes_presencas_unidade_id", "reunioes_presencas", ["unidade_id"])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_reunioes_presencas_unidade_id", table_name="reunioes_presencas")
    op.drop_index("ix_reunioes_presencas_reuniao_id", table_name="reunioes_presencas")
    op.drop_table("reunioes_presencas")

    op.drop_index("ix_reunioes_data_hora", table_name="reunioes")
    op.drop_index("ix_reunioes_predio_id", table_name="reunioes")
    op.drop_table("reunioes")

    status_reuniao_enum.drop(bind, checkfirst=True)
    tipo_reuniao_enum.drop(bind, checkfirst=True)
