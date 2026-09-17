"""Consulta de CEP via ViaCEP (API pública, gratuita, sem chave).

Usado só no cadastro de um `Predio`: preenche logradouro/bairro/cidade/uf a
partir do CEP informado pelo administrador, para não depender de digitação
manual do endereço completo. O resultado é gravado no `Predio` (não
recalculado a cada leitura) — o sistema continua funcionando normalmente
mesmo se o ViaCEP ficar fora do ar depois do cadastro.
"""
from __future__ import annotations

import re

import httpx

_CEP_RE = re.compile(r"^\d{8}$")


class CepInvalidoError(ValueError):
    """CEP com formato inválido (não são 8 dígitos)."""


class CepNaoEncontradoError(ValueError):
    """CEP com formato válido, mas o ViaCEP não encontrou endereço para ele."""


class CepServicoIndisponivelError(RuntimeError):
    """Timeout ou erro de rede ao consultar o ViaCEP."""


def normalizar_cep(cep: str) -> str:
    apenas_digitos = re.sub(r"\D", "", cep)
    if not _CEP_RE.match(apenas_digitos):
        raise CepInvalidoError("CEP deve ter 8 digitos.")
    return apenas_digitos


class EnderecoViaCep:
    __slots__ = ("logradouro", "bairro", "cidade", "uf")

    def __init__(self, *, logradouro: str, bairro: str, cidade: str, uf: str) -> None:
        self.logradouro = logradouro
        self.bairro = bairro
        self.cidade = cidade
        self.uf = uf


def consultar_cep(cep: str, *, timeout: float = 5.0) -> EnderecoViaCep:
    """Consulta https://viacep.com.br/ws/{cep}/json/. Lança
    `CepInvalidoError`, `CepNaoEncontradoError` ou `CepServicoIndisponivelError`
    conforme o caso - o chamador decide o status HTTP apropriado para cada um."""
    cep_normalizado = normalizar_cep(cep)

    try:
        response = httpx.get(
            f"https://viacep.com.br/ws/{cep_normalizado}/json/", timeout=timeout
        )
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise CepServicoIndisponivelError(
            "Nao foi possivel consultar o CEP no momento. Tente novamente."
        ) from exc

    if data.get("erro"):
        raise CepNaoEncontradoError(f"CEP {cep_normalizado} nao encontrado.")

    return EnderecoViaCep(
        logradouro=data.get("logradouro") or "",
        bairro=data.get("bairro") or "",
        cidade=data.get("localidade") or "",
        uf=data.get("uf") or "",
    )
