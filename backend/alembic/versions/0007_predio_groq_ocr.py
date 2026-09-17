"""troca do provedor de OCR: Gemini -> Groq (Fase 2 - motor financeiro)

Revision ID: 0007_predio_groq_ocr
Revises: 0006_predio_gemini_ocr
Create Date: 2026-09-17

Substitui o provedor de OCR de boletos de Gemini para Groq (API compativel
com o formato OpenAI, modelos com visao). Cada predio continua com sua
propria chave (conta do proprio condominio) - só o provedor muda, o desenho
de "uma chave cifrada por predio" continua o mesmo, daí o rename de coluna
em vez de um esquema novo.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_predio_groq_ocr"
down_revision: Union[str, None] = "0006_predio_gemini_ocr"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("predios", "gemini_api_key_cifrada", new_column_name="groq_api_key_cifrada")


def downgrade() -> None:
    op.alter_column("predios", "groq_api_key_cifrada", new_column_name="gemini_api_key_cifrada")
