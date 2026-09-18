"""tickets de atendimento (Fase 3 - comunicacao/transparencia)

Revision ID: 0009_tickets_atendimento
Revises: 0008_despesa_comprovante_url
Create Date: 2026-09-18

Modulo de chamados de manutencao/duvida/solicitacao com SLA por
prioridade (ver app/core/tickets.py) e uma thread de comentarios simples.
Criado DEPOIS da migration de multi-tenancy (0004) - ao contrario de
fornecedores/despesas, `predio_id` ja nasce NOT NULL, sem precisar de
backfill (tabela nova, sem linhas legadas).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0009_tickets_atendimento"
down_revision: Union[str, None] = "0008_despesa_comprovante_url"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

categoria_ticket_enum = postgresql.ENUM(
    "manutencao", "duvida", "solicitacao", "outro", name="categoria_ticket_enum"
)
prioridade_ticket_enum = postgresql.ENUM("baixa", "media", "alta", name="prioridade_ticket_enum")
status_ticket_enum = postgresql.ENUM(
    "aberto", "em_andamento", "resolvido", "cancelado", name="status_ticket_enum"
)


def upgrade() -> None:
    # NAO criar os ENUMs manualmente aqui: o SQLAlchemy ja cria os tipos
    # automaticamente via create_table (mesma licao das migrations
    # anteriores - criar o ENUM antes causa DuplicateObject contra um
    # Postgres real).
    op.create_table(
        "tickets_atendimento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_tickets_atendimento_predio_id"),
            nullable=False,
        ),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey(
                "unidades.id", ondelete="SET NULL", name="fk_tickets_atendimento_unidade_id"
            ),
            nullable=True,
        ),
        sa.Column(
            "responsavel_id",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_tickets_atendimento_responsavel_id"
            ),
            nullable=True,
        ),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("categoria", categoria_ticket_enum, nullable=False),
        sa.Column("prioridade", prioridade_ticket_enum, nullable=False),
        sa.Column(
            "status",
            status_ticket_enum,
            nullable=False,
            server_default=sa.text("'aberto'::status_ticket_enum"),
        ),
        sa.Column("prazo_sla", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolvido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_tickets_atendimento_created_by"
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_tickets_atendimento_predio_id", "tickets_atendimento", ["predio_id"])
    op.create_index("ix_tickets_atendimento_unidade_id", "tickets_atendimento", ["unidade_id"])
    op.create_index(
        "ix_tickets_atendimento_responsavel_id", "tickets_atendimento", ["responsavel_id"]
    )

    op.create_table(
        "tickets_comentarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_tickets_comentarios_predio_id"),
            nullable=False,
        ),
        sa.Column(
            "ticket_id",
            sa.Integer(),
            sa.ForeignKey(
                "tickets_atendimento.id", ondelete="CASCADE", name="fk_tickets_comentarios_ticket_id"
            ),
            nullable=False,
        ),
        sa.Column("mensagem", sa.Text(), nullable=False),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_tickets_comentarios_created_by"
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_tickets_comentarios_predio_id", "tickets_comentarios", ["predio_id"])
    op.create_index("ix_tickets_comentarios_ticket_id", "tickets_comentarios", ["ticket_id"])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_tickets_comentarios_ticket_id", table_name="tickets_comentarios")
    op.drop_index("ix_tickets_comentarios_predio_id", table_name="tickets_comentarios")
    op.drop_table("tickets_comentarios")

    op.drop_index("ix_tickets_atendimento_responsavel_id", table_name="tickets_atendimento")
    op.drop_index("ix_tickets_atendimento_unidade_id", table_name="tickets_atendimento")
    op.drop_index("ix_tickets_atendimento_predio_id", table_name="tickets_atendimento")
    op.drop_table("tickets_atendimento")

    status_ticket_enum.drop(bind, checkfirst=True)
    prioridade_ticket_enum.drop(bind, checkfirst=True)
    categoria_ticket_enum.drop(bind, checkfirst=True)
