"""integracao Gemini OCR por predio (Fase 2 - motor financeiro)

Revision ID: 0006_predio_gemini_ocr
Revises: 0005_rateio_despesas
Create Date: 2026-09-17

Terceira fatia da Fase 2 (Motor Financeiro): cada prédio pode configurar sua
própria chave de API do Gemini (conta do condomínio, não uma chave global do
sistema) para o OCR de boletos/comprovantes. A chave é armazenada cifrada
(ver app/core/crypto.py) - nunca em texto plano.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_predio_gemini_ocr"
down_revision: Union[str, None] = "0005_rateio_despesas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "predios", sa.Column("gemini_api_key_cifrada", sa.String(500), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("predios", "gemini_api_key_cifrada")
