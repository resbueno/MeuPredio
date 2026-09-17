from __future__ import annotations

from decimal import Decimal

import httpx
import pytest

from app.core.groq_ocr import GroqIndisponivelError, extrair_dados_boleto


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def _payload_com_texto(texto: str) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": texto}}],
    }


def test_extrair_dados_boleto_com_sucesso(monkeypatch):
    texto_json = (
        '{"fornecedor_nome": "Companhia de Agua", "fornecedor_documento": "12345678000199", '
        '"valor": "150.75", "data_vencimento": "2026-11-10", "linha_digitavel": "12345 67890", '
        '"descricao_sugerida": "Conta de agua", "categoria_sugerida": "agua"}'
    )

    def _fake_post(url, *, headers, json, timeout):
        assert headers["Authorization"] == "Bearer chave-de-teste"
        conteudo = json["messages"][0]["content"]
        assert conteudo[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
        return _FakeResponse(_payload_com_texto(texto_json))

    monkeypatch.setattr("app.core.groq_ocr.httpx.post", _fake_post)

    resultado = extrair_dados_boleto(api_key="chave-de-teste", conteudo=b"fake-bytes", mime_type="image/jpeg")

    assert resultado.fornecedor_nome == "Companhia de Agua"
    assert resultado.valor == Decimal("150.75")
    assert resultado.categoria_sugerida == "agua"


def test_extrair_dados_boleto_com_campos_nulos(monkeypatch):
    texto_json = (
        '{"fornecedor_nome": null, "fornecedor_documento": null, "valor": null, '
        '"data_vencimento": null, "linha_digitavel": null, "descricao_sugerida": null, '
        '"categoria_sugerida": null}'
    )
    monkeypatch.setattr(
        "app.core.groq_ocr.httpx.post",
        lambda *a, **k: _FakeResponse(_payload_com_texto(texto_json)),
    )

    resultado = extrair_dados_boleto(api_key="x", conteudo=b"x", mime_type="image/png")
    assert resultado.fornecedor_nome is None
    assert resultado.valor is None


def test_erro_de_rede_vira_groq_indisponivel_error(monkeypatch):
    def _fake_post(*args, **kwargs):
        raise httpx.ConnectError("falha de rede")

    monkeypatch.setattr("app.core.groq_ocr.httpx.post", _fake_post)

    with pytest.raises(GroqIndisponivelError):
        extrair_dados_boleto(api_key="x", conteudo=b"x", mime_type="image/png")


def test_resposta_sem_choices_vira_groq_indisponivel_error(monkeypatch):
    payload = {"choices": []}
    monkeypatch.setattr("app.core.groq_ocr.httpx.post", lambda *a, **k: _FakeResponse(payload))

    with pytest.raises(GroqIndisponivelError):
        extrair_dados_boleto(api_key="x", conteudo=b"x", mime_type="image/png")


def test_json_malformado_vira_groq_indisponivel_error(monkeypatch):
    monkeypatch.setattr(
        "app.core.groq_ocr.httpx.post",
        lambda *a, **k: _FakeResponse(_payload_com_texto("isto nao e json")),
    )

    with pytest.raises(GroqIndisponivelError):
        extrair_dados_boleto(api_key="x", conteudo=b"x", mime_type="image/png")
