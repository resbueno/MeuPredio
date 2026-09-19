"""modulo de visitantes e reserva de espacos (areas comuns)

Revision ID: 0014_visitantes_reservas
Revises: 0013_notificacoes_entregas
Create Date: 2026-09-19

Visitante: log de entrada na portaria (append-only), visivel so a
zelador/sindico/administrador. AreaComum: espaco reservavel cadastrado
pela gestao, com `agenda_liberada_ate` controlando ate quando a agenda
esta aberta para reserva. Reserva: uma unidade reserva uma AreaComum para
um dia inteiro - indice parcial unico (area_comum_id, data) WHERE
status='confirmada' impede dupla reserva confirmada no mesmo dia.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0014_visitantes_reservas"
down_revision: Union[str, None] = "0013_notificacoes_entregas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tipo_documento_visitante_enum = postgresql.ENUM(
    "rg", "cpf", "cin", "nao_informado", name="tipo_documento_visitante_enum"
)
status_reserva_enum = postgresql.ENUM("confirmada", "cancelada", name="status_reserva_enum")


def upgrade() -> None:
    # NAO criar os ENUMs manualmente aqui: o SQLAlchemy ja cria os tipos
    # automaticamente via create_table (mesma licao das migrations
    # anteriores - criar o ENUM antes causa DuplicateObject contra um
    # Postgres real).
    op.create_table(
        "visitantes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_visitantes_predio_id"),
            nullable=False,
        ),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey("unidades.id", ondelete="CASCADE", name="fk_visitantes_unidade_id"),
            nullable=False,
        ),
        sa.Column("nome_completo", sa.String(255), nullable=False),
        sa.Column("tipo_documento", tipo_documento_visitante_enum, nullable=False),
        sa.Column("numero_documento", sa.String(50), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_visitantes_created_by"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_visitantes_predio_id", "visitantes", ["predio_id"])
    op.create_index("ix_visitantes_unidade_id", "visitantes", ["unidade_id"])

    op.create_table(
        "areas_comuns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_areas_comuns_predio_id"),
            nullable=False,
        ),
        sa.Column("nome", sa.String(150), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("capacidade", sa.Integer(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("agenda_liberada_ate", sa.Date(), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_areas_comuns_created_by"),
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
    op.create_index("ix_areas_comuns_predio_id", "areas_comuns", ["predio_id"])

    op.create_table(
        "reservas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_reservas_predio_id"),
            nullable=False,
        ),
        sa.Column(
            "area_comum_id",
            sa.Integer(),
            sa.ForeignKey("areas_comuns.id", ondelete="CASCADE", name="fk_reservas_area_comum_id"),
            nullable=False,
        ),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey("unidades.id", ondelete="CASCADE", name="fk_reservas_unidade_id"),
            nullable=False,
        ),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column(
            "status",
            status_reserva_enum,
            nullable=False,
            server_default=sa.text("'confirmada'::status_reserva_enum"),
        ),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("cancelada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cancelada_por",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_reservas_cancelada_por"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_reservas_created_by"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_reservas_predio_id", "reservas", ["predio_id"])
    op.create_index("ix_reservas_area_comum_id", "reservas", ["area_comum_id"])
    op.create_index("ix_reservas_unidade_id", "reservas", ["unidade_id"])
    op.create_index("ix_reservas_data", "reservas", ["data"])
    op.create_index(
        "uq_reservas_area_data_confirmada",
        "reservas",
        ["area_comum_id", "data"],
        unique=True,
        postgresql_where=sa.text("status = 'confirmada'"),
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("uq_reservas_area_data_confirmada", table_name="reservas")
    op.drop_index("ix_reservas_data", table_name="reservas")
    op.drop_index("ix_reservas_unidade_id", table_name="reservas")
    op.drop_index("ix_reservas_area_comum_id", table_name="reservas")
    op.drop_index("ix_reservas_predio_id", table_name="reservas")
    op.drop_table("reservas")

    op.drop_index("ix_areas_comuns_predio_id", table_name="areas_comuns")
    op.drop_table("areas_comuns")

    op.drop_index("ix_visitantes_unidade_id", table_name="visitantes")
    op.drop_index("ix_visitantes_predio_id", table_name="visitantes")
    op.drop_table("visitantes")

    status_reserva_enum.drop(bind, checkfirst=True)
    tipo_documento_visitante_enum.drop(bind, checkfirst=True)
