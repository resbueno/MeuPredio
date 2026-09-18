"""comprovante de pagamento em despesas_lancamentos

Revision ID: 0008_despesa_comprovante_url
Revises: 0007_predio_groq_ocr
Create Date: 2026-09-18

Campo separado de `documento_url` (o boleto/comprovante original, anexado
na criacao) - `comprovante_pagamento_url` guarda o comprovante da baixa em
si (recibo, print do PIX/TED), anexavel a qualquer momento depois que o
lancamento vira "pago" (ver POST /despesas/{id}/comprovante).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008_despesa_comprovante_url"
down_revision: Union[str, None] = "0007_predio_groq_ocr"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "despesas_lancamentos",
        sa.Column("comprovante_pagamento_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("despesas_lancamentos", "comprovante_pagamento_url")
