"""schema inicial: usuarios, unidades, veiculos, logs_auditoria

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-09-16

Observação sobre a referência circular usuarios.unidade_id <-> unidades.proprietario_id:
1) criamos "usuarios" (com a coluna unidade_id, mas SEM a FK ainda);
2) criamos "unidades" (cuja FK proprietario_id -> usuarios.id já pode existir,
   pois "usuarios" já existe nesse ponto);
3) só então adicionamos a FK usuarios.unidade_id -> unidades.id via ALTER TABLE.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

role_enum = postgresql.ENUM(
    "morador", "sindico", "zelador", "administrador", name="role_enum"
)
tipo_veiculo_enum = postgresql.ENUM("carro", "moto", "outro", name="tipo_veiculo_enum")


def upgrade() -> None:
    bind = op.get_bind()
    role_enum.create(bind, checkfirst=True)
    tipo_veiculo_enum.create(bind, checkfirst=True)

    # --- usuarios (sem a FK de unidade_id ainda) ---
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "role",
            role_enum,
            nullable=False,
            server_default=sa.text("'morador'::role_enum"),
        ),
        sa.Column("unidade_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("consent_lgpd_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_usuarios_created_by"),
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
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    # --- unidades ---
    op.create_table(
        "unidades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bloco", sa.String(20), nullable=False),
        sa.Column("numero", sa.String(20), nullable=False),
        sa.Column(
            "proprietario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_unidades_proprietario_id"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_unidades_created_by"),
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
        sa.UniqueConstraint("bloco", "numero", name="uq_unidades_bloco_numero"),
    )

    # Fecha o ciclo: usuarios.unidade_id -> unidades.id
    op.create_foreign_key(
        "fk_usuarios_unidade_id",
        "usuarios",
        "unidades",
        ["unidade_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- veiculos ---
    op.create_table(
        "veiculos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey("unidades.id", ondelete="CASCADE", name="fk_veiculos_unidade_id"),
            nullable=False,
        ),
        sa.Column("placa", sa.String(10), nullable=False),
        sa.Column("modelo", sa.String(100), nullable=False),
        sa.Column("cor", sa.String(40), nullable=False),
        sa.Column(
            "tipo",
            tipo_veiculo_enum,
            nullable=False,
            server_default=sa.text("'carro'::tipo_veiculo_enum"),
        ),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_veiculos_created_by"),
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
    op.create_index("ix_veiculos_placa", "veiculos", ["placa"])

    # --- logs_auditoria (a imutabilidade é adicionada na próxima migration) ---
    op.create_table(
        "logs_auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_logs_auditoria_usuario_id"),
            nullable=True,
        ),
        sa.Column("acao", sa.String(50), nullable=False),
        sa.Column("entidade", sa.String(100), nullable=False),
        sa.Column("entidade_id", sa.Integer(), nullable=True),
        sa.Column("dados_antes", postgresql.JSONB(), nullable=True),
        sa.Column("dados_depois", postgresql.JSONB(), nullable=True),
        sa.Column("ip_origem", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_logs_auditoria_entidade", "logs_auditoria", ["entidade", "entidade_id"])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_logs_auditoria_entidade", table_name="logs_auditoria")
    op.drop_table("logs_auditoria")

    op.drop_index("ix_veiculos_placa", table_name="veiculos")
    op.drop_table("veiculos")

    op.drop_constraint("fk_usuarios_unidade_id", "usuarios", type_="foreignkey")
    op.drop_table("unidades")

    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_table("usuarios")

    tipo_veiculo_enum.drop(bind, checkfirst=True)
    role_enum.drop(bind, checkfirst=True)
