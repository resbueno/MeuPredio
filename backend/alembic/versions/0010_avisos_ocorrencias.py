"""mural de avisos, avisos diretos/multas e livro de ocorrencias

Revision ID: 0010_avisos_ocorrencias
Revises: 0009_tickets_atendimento
Create Date: 2026-09-19

Tres tabelas novas (avisos_mural, avisos_diretos, livro_ocorrencias), todas
ja nascendo com predio_id NOT NULL (mesmo caso de tickets_atendimento na
0009). Alem disso, `despesas_lancamentos` ganha `unidade_id` nullable: nulo
continua sendo a despesa geral ratejada entre unidades (comportamento atual
inalterado); preenchido marca uma despesa EXCLUSIVA de uma unidade (a multa
gerada por um aviso direto tipo 'multa' e o primeiro uso disso).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0010_avisos_ocorrencias"
down_revision: Union[str, None] = "0009_tickets_atendimento"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tipo_aviso_mural_enum = postgresql.ENUM(
    "condominio", "anuncio", name="tipo_aviso_mural_enum"
)
destinatario_aviso_enum = postgresql.ENUM(
    "morador", "proprietario", "ambos", name="destinatario_aviso_enum"
)
tipo_aviso_direto_enum = postgresql.ENUM(
    "aviso", "advertencia", "multa", name="tipo_aviso_direto_enum"
)


def upgrade() -> None:
    op.add_column(
        "despesas_lancamentos",
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey(
                "unidades.id", ondelete="SET NULL", name="fk_despesas_lancamentos_unidade_id"
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_despesas_lancamentos_unidade_id", "despesas_lancamentos", ["unidade_id"]
    )

    # NAO criar os ENUMs manualmente aqui: o SQLAlchemy ja cria os tipos
    # automaticamente via create_table (mesma licao das migrations
    # anteriores - criar o ENUM antes causa DuplicateObject contra um
    # Postgres real).
    op.create_table(
        "avisos_mural",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_avisos_mural_predio_id"),
            nullable=False,
        ),
        sa.Column("tipo", tipo_aviso_mural_enum, nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("preco", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_avisos_mural_created_by"),
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
    op.create_index("ix_avisos_mural_predio_id", "avisos_mural", ["predio_id"])
    op.create_index("ix_avisos_mural_tipo", "avisos_mural", ["tipo"])

    op.create_table(
        "avisos_diretos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_avisos_diretos_predio_id"),
            nullable=False,
        ),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey("unidades.id", ondelete="CASCADE", name="fk_avisos_diretos_unidade_id"),
            nullable=False,
        ),
        sa.Column("destinatario", destinatario_aviso_enum, nullable=False),
        sa.Column("tipo", tipo_aviso_direto_enum, nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("mensagem", sa.Text(), nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "despesa_lancamento_id",
            sa.Integer(),
            sa.ForeignKey(
                "despesas_lancamentos.id",
                ondelete="SET NULL",
                name="fk_avisos_diretos_despesa_lancamento_id",
            ),
            nullable=True,
        ),
        sa.Column("lida_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resposta", sa.Text(), nullable=True),
        sa.Column(
            "respondido_por",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_avisos_diretos_respondido_por"
            ),
            nullable=True,
        ),
        sa.Column("respondido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_avisos_diretos_created_by"),
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
    op.create_index("ix_avisos_diretos_predio_id", "avisos_diretos", ["predio_id"])
    op.create_index("ix_avisos_diretos_unidade_id", "avisos_diretos", ["unidade_id"])
    op.create_index("ix_avisos_diretos_tipo", "avisos_diretos", ["tipo"])

    op.create_table(
        "livro_ocorrencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_livro_ocorrencias_predio_id"),
            nullable=False,
        ),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey(
                "unidades.id", ondelete="SET NULL", name="fk_livro_ocorrencias_unidade_id"
            ),
            nullable=True,
        ),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("editado_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "editado_por",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_livro_ocorrencias_editado_por"
            ),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_livro_ocorrencias_created_by"
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
    op.create_index("ix_livro_ocorrencias_predio_id", "livro_ocorrencias", ["predio_id"])
    op.create_index("ix_livro_ocorrencias_unidade_id", "livro_ocorrencias", ["unidade_id"])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_livro_ocorrencias_unidade_id", table_name="livro_ocorrencias")
    op.drop_index("ix_livro_ocorrencias_predio_id", table_name="livro_ocorrencias")
    op.drop_table("livro_ocorrencias")

    op.drop_index("ix_avisos_diretos_tipo", table_name="avisos_diretos")
    op.drop_index("ix_avisos_diretos_unidade_id", table_name="avisos_diretos")
    op.drop_index("ix_avisos_diretos_predio_id", table_name="avisos_diretos")
    op.drop_table("avisos_diretos")
    tipo_aviso_direto_enum.drop(bind, checkfirst=True)
    destinatario_aviso_enum.drop(bind, checkfirst=True)

    op.drop_index("ix_avisos_mural_tipo", table_name="avisos_mural")
    op.drop_index("ix_avisos_mural_predio_id", table_name="avisos_mural")
    op.drop_table("avisos_mural")
    tipo_aviso_mural_enum.drop(bind, checkfirst=True)

    op.drop_index("ix_despesas_lancamentos_unidade_id", table_name="despesas_lancamentos")
    op.drop_column("despesas_lancamentos", "unidade_id")
