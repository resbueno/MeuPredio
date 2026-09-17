from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ExtracaoBoletoResponse(BaseModel):
    """Resultado da extração (não persiste nada) - o chamador revisa/corrige
    os campos e então cria a despesa via `POST /despesas` normalmente,
    passando `documento_url` de volta."""

    documento_url: str
    fornecedor_nome: str | None = None
    fornecedor_documento: str | None = None
    valor: Decimal | None = None
    data_vencimento: date | None = None
    linha_digitavel: str | None = None
    descricao_sugerida: str | None = None
    categoria_sugerida: str | None = None
