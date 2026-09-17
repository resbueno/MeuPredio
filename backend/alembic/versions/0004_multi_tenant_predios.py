"""multi-tenancy: predios, convites, unidades/usuarios/fornecedores/despesas escopados por predio

Revision ID: 0004_multi_tenant_predios
Revises: 0003_fornecedores_despesas
Create Date: 2026-09-17

Introduz `Predio` como raiz do isolamento multi-tenant: login passa a exigir
identificar o prédio (CEP+número) antes de e-mail/senha, e todo dado de
negócio (unidades, usuários exceto administrador, fornecedores, despesas)
passa a pertencer a exatamente um prédio. Um prédio nunca enxerga dados de
outro.

Mudanças de modelagem que valem destacar:
- `unidades.proprietario_id` é REMOVIDO: "quem é dono/mora em uma unidade"
  passa a ser modelado do lado de `usuarios`, via a relação N:N
  `usuario_unidades` + o papel (`role`) de cada usuário - uma pessoa pode
  ter mais de uma unidade, e uma unidade pode ter mais de um
  morador/proprietário, sem duas fontes de verdade concorrentes.
- `usuarios.unidade_id` (FK única) também é REMOVIDO em favor da mesma
  relação N:N `usuario_unidades`.
- `usuarios.email` deixa de ser globalmente único: agora é único DENTRO do
  prédio (dois prédios são tenants isolados) e único globalmente só entre
  administradores (papel sem prédio) - dois índices únicos parciais, porque
  um UniqueConstraint(predio_id, email) comum não pegaria dois
  administradores com o mesmo e-mail (Postgres trata cada NULL como
  distinto).
- Novo papel `proprietario` no enum `role_enum` (ALTER TYPE ADD VALUE).

Dado que este é um estágio inicial do produto (sem base de clientes real
ainda - ver histórico de deploy em homologação), as novas colunas
`predio_id` entram diretamente como NOT NULL onde fazem sentido
(unidades/fornecedores/despesas), sem uma etapa de backfill: não há por
enquanto uma migration de dados de produção genuína para preservar aqui.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_multi_tenant_predios"
down_revision: Union[str, None] = "0003_fornecedores_despesas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- novo papel no enum existente ---
    op.execute("ALTER TYPE role_enum ADD VALUE IF NOT EXISTS 'proprietario'")

    # --- predios ---
    op.create_table(
        "predios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("cep", sa.String(8), nullable=False),
        sa.Column("numero", sa.String(20), nullable=False),
        sa.Column("complemento", sa.String(100), nullable=True),
        sa.Column("logradouro", sa.String(255), nullable=True),
        sa.Column("bairro", sa.String(100), nullable=True),
        sa.Column("cidade", sa.String(100), nullable=True),
        sa.Column("uf", sa.String(2), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_predios_created_by"),
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
        sa.UniqueConstraint("cep", "numero", name="uq_predios_cep_numero"),
    )
    op.create_index("ix_predios_cep", "predios", ["cep"])

    # --- predio_convites ---
    op.create_table(
        "predio_convites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "predio_id",
            sa.Integer(),
            sa.ForeignKey("predios.id", ondelete="CASCADE", name="fk_predio_convites_predio_id"),
            nullable=False,
        ),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("expira_em", sa.Date(), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="SET NULL", name="fk_predio_convites_created_by"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_predio_convites_predio_id", "predio_convites", ["predio_id"])
    op.create_index("ix_predio_convites_token", "predio_convites", ["token"], unique=True)

    # --- unidades: predio_id + remoção de proprietario_id ---
    op.add_column("unidades", sa.Column("predio_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE unidades SET predio_id = (SELECT id FROM predios ORDER BY id LIMIT 1) "
        "WHERE predio_id IS NULL"
    )
    # Sem prédio nenhum cadastrado ainda (base nova) e alguma unidade
    # preexistente: não há como inferir o prédio - aborta em vez de deixar
    # unidades "orfãs" de tenant.
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM unidades WHERE predio_id IS NULL) THEN "
        "RAISE EXCEPTION 'Existem unidades sem predio para migrar - backfill manual necessario'; "
        "END IF; END $$;"
    )
    op.alter_column("unidades", "predio_id", nullable=False)
    op.create_foreign_key(
        "fk_unidades_predio_id", "unidades", "predios", ["predio_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_unidades_predio_id", "unidades", ["predio_id"])
    op.drop_constraint("fk_unidades_proprietario_id", "unidades", type_="foreignkey")
    op.drop_constraint("uq_unidades_bloco_numero", "unidades", type_="unique")
    op.drop_column("unidades", "proprietario_id")
    op.create_unique_constraint(
        "uq_unidades_predio_bloco_numero", "unidades", ["predio_id", "bloco", "numero"]
    )

    # --- usuarios: predio_id + remoção de unidade_id + email escopado ---
    op.add_column("usuarios", sa.Column("predio_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_usuarios_predio_id", "usuarios", "predios", ["predio_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_usuarios_predio_id", "usuarios", ["predio_id"])
    op.drop_constraint("fk_usuarios_unidade_id", "usuarios", type_="foreignkey")
    op.drop_column("usuarios", "unidade_id")

    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.create_index("ix_usuarios_email", "usuarios", ["email"])
    op.create_index(
        "uq_usuarios_email_por_predio",
        "usuarios",
        ["predio_id", "email"],
        unique=True,
        postgresql_where=sa.text("predio_id IS NOT NULL"),
    )
    op.create_index(
        "uq_usuarios_email_administrador",
        "usuarios",
        ["email"],
        unique=True,
        postgresql_where=sa.text("predio_id IS NULL"),
    )
    op.create_check_constraint(
        "ck_usuarios_administrador_sem_predio",
        "usuarios",
        "(role = 'administrador'::role_enum AND predio_id IS NULL) "
        "OR (role <> 'administrador'::role_enum AND predio_id IS NOT NULL)",
    )

    # --- usuario_unidades (N:N) ---
    op.create_table(
        "usuario_unidades",
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", ondelete="CASCADE", name="fk_usuario_unidades_usuario_id"),
            primary_key=True,
        ),
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey("unidades.id", ondelete="CASCADE", name="fk_usuario_unidades_unidade_id"),
            primary_key=True,
        ),
    )

    # --- fornecedores: predio_id + unicidade de documento escopada ---
    op.add_column("fornecedores", sa.Column("predio_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE fornecedores SET predio_id = (SELECT id FROM predios ORDER BY id LIMIT 1) "
        "WHERE predio_id IS NULL"
    )
    op.alter_column("fornecedores", "predio_id", nullable=False)
    op.create_foreign_key(
        "fk_fornecedores_predio_id", "fornecedores", "predios", ["predio_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_fornecedores_predio_id", "fornecedores", ["predio_id"])
    op.drop_constraint("uq_fornecedores_documento", "fornecedores", type_="unique")
    op.create_index(
        "uq_fornecedores_predio_documento",
        "fornecedores",
        ["predio_id", "documento"],
        unique=True,
    )

    # --- despesas_lancamentos: predio_id ---
    op.add_column("despesas_lancamentos", sa.Column("predio_id", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE despesas_lancamentos SET predio_id = (SELECT id FROM predios ORDER BY id LIMIT 1) "
        "WHERE predio_id IS NULL"
    )
    op.alter_column("despesas_lancamentos", "predio_id", nullable=False)
    op.create_foreign_key(
        "fk_despesas_lancamentos_predio_id",
        "despesas_lancamentos",
        "predios",
        ["predio_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_despesas_lancamentos_predio_id", "despesas_lancamentos", ["predio_id"])


def downgrade() -> None:
    op.drop_index("ix_despesas_lancamentos_predio_id", table_name="despesas_lancamentos")
    op.drop_constraint("fk_despesas_lancamentos_predio_id", "despesas_lancamentos", type_="foreignkey")
    op.drop_column("despesas_lancamentos", "predio_id")

    op.drop_index("uq_fornecedores_predio_documento", table_name="fornecedores")
    op.create_unique_constraint("uq_fornecedores_documento", "fornecedores", ["documento"])
    op.drop_index("ix_fornecedores_predio_id", table_name="fornecedores")
    op.drop_constraint("fk_fornecedores_predio_id", "fornecedores", type_="foreignkey")
    op.drop_column("fornecedores", "predio_id")

    op.drop_table("usuario_unidades")

    op.drop_constraint("ck_usuarios_administrador_sem_predio", "usuarios", type_="check")
    op.drop_index("uq_usuarios_email_administrador", table_name="usuarios")
    op.drop_index("uq_usuarios_email_por_predio", table_name="usuarios")
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)
    op.add_column(
        "usuarios",
        sa.Column(
            "unidade_id",
            sa.Integer(),
            sa.ForeignKey("unidades.id", ondelete="SET NULL", name="fk_usuarios_unidade_id", use_alter=True),
            nullable=True,
        ),
    )
    op.drop_index("ix_usuarios_predio_id", table_name="usuarios")
    op.drop_constraint("fk_usuarios_predio_id", "usuarios", type_="foreignkey")
    op.drop_column("usuarios", "predio_id")

    op.create_unique_constraint("uq_unidades_bloco_numero", "unidades", ["bloco", "numero"])
    op.drop_constraint("uq_unidades_predio_bloco_numero", "unidades", type_="unique")
    op.add_column("unidades", sa.Column("proprietario_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_unidades_proprietario_id",
        "unidades",
        "usuarios",
        ["proprietario_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_index("ix_unidades_predio_id", table_name="unidades")
    op.drop_constraint("fk_unidades_predio_id", "unidades", type_="foreignkey")
    op.drop_column("unidades", "predio_id")

    op.drop_index("ix_predio_convites_token", table_name="predio_convites")
    op.drop_index("ix_predio_convites_predio_id", table_name="predio_convites")
    op.drop_table("predio_convites")

    op.drop_index("ix_predios_cep", table_name="predios")
    op.drop_table("predios")

    # Postgres não suporta DROP VALUE de um enum - o valor 'proprietario'
    # permanece no tipo mesmo após o downgrade (limitação conhecida/aceita).
