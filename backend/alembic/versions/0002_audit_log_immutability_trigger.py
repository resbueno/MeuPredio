"""trigger de imutabilidade em logs_auditoria (bloqueia UPDATE/DELETE)

Revision ID: 0002_audit_log_immutability_trigger
Revises: 0001_initial_schema
Create Date: 2026-09-16

Esta migration é o coração do requisito de auditoria imutável: mesmo que a
camada de aplicação seja comprometida (bug, acesso direto ao banco com a
credencial da app, etc.), o PostgreSQL em si recusa qualquer UPDATE ou DELETE
em `logs_auditoria`. Só é possível inserir novas linhas.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_audit_log_immutability_trigger"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION fn_logs_auditoria_bloquear_alteracao()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION
        'logs_auditoria e imutavel: % nao e permitido (tabela=%, tentativa em id=%)',
        TG_OP, TG_TABLE_NAME, OLD.id
        USING ERRCODE = '23000';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""

_DROP_FUNCTION_SQL = "DROP FUNCTION IF EXISTS fn_logs_auditoria_bloquear_alteracao();"

_TRIGGER_UPDATE_SQL = """
CREATE TRIGGER trg_logs_auditoria_bloquear_update
BEFORE UPDATE ON logs_auditoria
FOR EACH ROW
EXECUTE FUNCTION fn_logs_auditoria_bloquear_alteracao();
"""

_TRIGGER_DELETE_SQL = """
CREATE TRIGGER trg_logs_auditoria_bloquear_delete
BEFORE DELETE ON logs_auditoria
FOR EACH ROW
EXECUTE FUNCTION fn_logs_auditoria_bloquear_alteracao();
"""


def upgrade() -> None:
    op.execute(_FUNCTION_SQL)
    op.execute(_TRIGGER_UPDATE_SQL)
    op.execute(_TRIGGER_DELETE_SQL)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_logs_auditoria_bloquear_update ON logs_auditoria;")
    op.execute("DROP TRIGGER IF EXISTS trg_logs_auditoria_bloquear_delete ON logs_auditoria;")
    op.execute(_DROP_FUNCTION_SQL)
