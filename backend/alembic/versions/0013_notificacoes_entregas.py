"""sino de alertas (notificacoes) e modulo de entregas

Revision ID: 0013_notificacoes_entregas
Revises: 0012_reunioes
Create Date: 2026-09-18

Notificacao: fan-out por destinatario (uma linha por usuario) gerado a
partir de avisos, ocorrencias, reunioes e entregas - ver
app/core/notificacoes.py. Entrega: encomenda recebida na portaria para uma
unidade, registrada por zelador/sindico/administrador.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0013_notificacoes_entregas"
down_revision: Union[str, None] = "0012_reunioes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tipo_notificacao_enum = postgresql.ENUM(
    "aviso_geral", "aviso_direto", "ocorrencia", "reuniao", "entrega", name="tipo_notificacao_enum"
)


def upgrade() -> None:
    # NAO criar o ENUM manualmente aqui: o SQLAlchemy ja cria o tipo
    # automaticamente via create_table (mesma licao das migrations
    # anteriores - criar o ENUM antes causa DuplicateObject contra um
    # Postgres real).
    op.create_table(
        "notificacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_notificacoes_predio_id"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE", name="fk_notificacoes_usuario_id"),
            nullable=False,
        ),
        sa.Column("tipo", tipo_notificacao_enum, nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("mensagem", sa.Text(), nullable=False),
        sa.Column("referencia_tipo", sa.String(50), nullable=True),
        sa.Column("referencia_id", sa.Integer(), nullable=True),
        sa.Column("lida_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_notificacoes_predio_id", "notificacoes", ["predio_id"])
    op.create_index("ix_notificacoes_usuario_id", "notificacoes", ["usuario_id"])
    op.create_index("ix_notificacoes_tipo", "notificacoes", ["tipo"])

    op.create_table(
        "entregas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_entregas_predio_id"),
            nullable=False,
        ),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey("unidades.id", ondelete="CASCADE", name="fk_entregas_unidade_id"),
            nullable=False,
        ),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("localizacao", sa.String(255), nullable=False),
        sa.Column("retirada_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "retirada_por",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_entregas_retirada_por"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_entregas_created_by"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_entregas_predio_id", "entregas", ["predio_id"])
    op.create_index("ix_entregas_unidade_id", "entregas", ["unidade_id"])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_entregas_unidade_id", table_name="entregas")
    op.drop_index("ix_entregas_predio_id", table_name="entregas")
    op.drop_table("entregas")

    op.drop_index("ix_notificacoes_tipo", table_name="notificacoes")
    op.drop_index("ix_notificacoes_usuario_id", table_name="notificacoes")
    op.drop_index("ix_notificacoes_predio_id", table_name="notificacoes")
    op.drop_table("notificacoes")

    tipo_notificacao_enum.drop(bind, checkfirst=True)
