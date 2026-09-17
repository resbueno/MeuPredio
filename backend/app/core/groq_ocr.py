"""Extração de dados de boletos/comprovantes via Groq API (endpoint
compatível com o formato OpenAI, `POST /openai/v1/chat/completions`) -
Fase 2, fatia de OCR do Motor Financeiro.

Chama a API REST diretamente com `httpx` (mesmo padrão de
`app/core/viacep.py`), contrato validado manualmente contra a API real:
auth via `Authorization: Bearer`, imagem via `image_url` com data URI
base64, `response_format: {"type": "json_object"}` para saída em JSON.

Só imagem, sem PDF: o único modelo com visão disponível nesta conta
(`qwen/qwen3.8-27b`) não aceita documento, apenas `image` em
`input_modalities` - PDF fica fora do escopo desta fatia (ver validação de
mime type em `app/routers/despesas.py`).

`json_object` (não `json_schema`/structured outputs) porque o modelo com
visão disponível não está entre os que suportam saída estruturada com
schema (`supported_features` não inclui `structured_outputs`) - o schema
exato é descrito no prompt, e a validação real do formato fica a cargo do
`ExtracaoBoleto.model_validate` do lado de cá.
"""
from __future__ import annotations

import base64
import json
from datetime import date
from decimal import Decimal

import httpx
from pydantic import BaseModel, ValidationError

_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODELO_PADRAO = "qwen/qwen3.8-27b"
# O tier gratuito desta API tem um limite curto de tokens de saida por
# minuto - a extracao so precisa de poucos campos curtos, entao um teto
# baixo evita estourar esse limite sem prejudicar o resultado.
_MAX_TOKENS = 500

_PROMPT = (
    "Este documento e um boleto ou comprovante de despesa de um condominio "
    "brasileiro. Extraia os campos abaixo e responda APENAS com um objeto "
    "JSON (sem markdown, sem texto adicional) com exatamente estas chaves, "
    "em portugues do Brasil. Quando um campo nao estiver presente ou "
    "legivel no documento, use null - nunca invente ou estime um valor.\n\n"
    "{\n"
    '  "fornecedor_nome": string ou null - nome do beneficiario/cedente do boleto,\n'
    '  "fornecedor_documento": string ou null - CPF ou CNPJ do beneficiario, so digitos,\n'
    '  "valor": string ou null - valor total a pagar, em reais, como numero decimal '
    "(sem 'R$' nem separador de milhar, ponto como separador decimal),\n"
    '  "data_vencimento": string ou null - data de vencimento no formato AAAA-MM-DD,\n'
    '  "linha_digitavel": string ou null - a linha digitavel/codigo de barras do boleto '
    "(so digitos e espacos), se houver,\n"
    '  "descricao_sugerida": string ou null - uma descricao curta e objetiva da despesa,\n'
    '  "categoria_sugerida": string ou null - uma palavra curta como \'agua\', \'luz\', '
    "'gas', 'condominio', 'manutencao' ou 'outros'\n"
    "}"
)


class ExtracaoBoleto(BaseModel):
    fornecedor_nome: str | None = None
    fornecedor_documento: str | None = None
    valor: Decimal | None = None
    data_vencimento: date | None = None
    linha_digitavel: str | None = None
    descricao_sugerida: str | None = None
    categoria_sugerida: str | None = None


class GroqIndisponivelError(RuntimeError):
    """Falha ao chamar a API do Groq (chave invalida, limite de taxa,
    sobrecarga temporaria do modelo, rede) - o chamador decide o status HTTP."""


def extrair_dados_boleto(
    *,
    api_key: str,
    conteudo: bytes,
    mime_type: str,
    modelo: str = _MODELO_PADRAO,
    timeout: float = 60.0,
) -> ExtracaoBoleto:
    data_uri = f"data:{mime_type};base64,{base64.b64encode(conteudo).decode('ascii')}"
    corpo = {
        "model": modelo,
        "max_tokens": _MAX_TOKENS,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _PROMPT},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ],
    }

    try:
        response = httpx.post(
            _CHAT_COMPLETIONS_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=corpo,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise GroqIndisponivelError(
            "Nao foi possivel processar o documento com o Groq no momento. Tente novamente."
        ) from exc

    try:
        texto = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GroqIndisponivelError(
            "O Groq nao retornou uma extracao para este documento."
        ) from exc

    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise GroqIndisponivelError(
            "O Groq retornou uma extracao em formato inesperado para este documento."
        ) from exc

    try:
        return ExtracaoBoleto.model_validate(dados)
    except ValidationError as exc:
        raise GroqIndisponivelError(
            "O Groq retornou dados em formato inesperado para este documento."
        ) from exc
