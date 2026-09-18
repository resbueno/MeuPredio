"""papeis adicionais por usuario (acumulo de funcoes no mesmo login)

Revision ID: 0011_usuarios_papeis_extras
Revises: 0010_avisos_ocorrencias
Create Date: 2026-09-20

Usuario.role continua sendo o papel PRINCIPAL (inclusive define
predio_id/unidades na criacao, como sempre) - esta tabela guarda papeis
ADICIONAIS que o mesmo login acumula (ex.: sindico que tambem e morador da
propria unidade). ADMINISTRADOR nunca aparece aqui, e' exclusivo (validado
na aplicacao, nao no banco - nao ha combinacao de tabelas que expresse essa
regra sem trigger dedicado, e o volume de escrita aqui nao justifica um).

Reaproveita o tipo `role_enum` ja existente (criado na 0001) - create_type
gerido pela migration inicial, aqui e' so o mesmo tipo aplicado numa coluna
nova.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0011_usuarios_papeis_extras"
down_revision: Union[str, None] = "0010_avisos_ocorrencias"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

role_enum = postgresql.ENUM(
    "morador",
    "proprietario",
    "sindico",
    "zelador",
    "administrador",
    name="role_enum",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "usuarios_papeis_extras",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="CASCADE", name="fk_usuarios_papeis_extras_usuario_id"
            ),
            nullable=False,
        ),
        sa.Column("role", role_enum, nullable=False),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey(
                "usuarios.id", ondelete="SET NULL", name="fk_usuarios_papeis_extras_created_by"
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("usuario_id", "role", name="uq_usuarios_papeis_extras_usuario_role"),
    )
    op.create_index(
        "ix_usuarios_papeis_extras_usuario_id", "usuarios_papeis_extras", ["usuario_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_usuarios_papeis_extras_usuario_id", table_name="usuarios_papeis_extras")
    op.drop_table("usuarios_papeis_extras")
