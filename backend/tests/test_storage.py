from __future__ import annotations

from app.core.storage import caminho_documento, salvar_documento


def test_salvar_documento_e_recuperar_pelo_caminho():
    documento_url = salvar_documento(predio_id=999, nome_original="boleto.jpg", conteudo=b"conteudo-fake")
    assert documento_url.startswith("despesas/documentos/999/")
    assert documento_url.endswith(".jpg")

    nome_arquivo = documento_url.rsplit("/", 1)[-1]
    caminho = caminho_documento(999, nome_arquivo)
    assert caminho is not None
    assert caminho.read_bytes() == b"conteudo-fake"


def test_caminho_documento_rejeita_nome_fora_do_padrao():
    assert caminho_documento(999, "../../etc/passwd") is None
    assert caminho_documento(999, "qualquer-coisa.jpg") is None


def test_caminho_documento_inexistente_retorna_none():
    assert caminho_documento(999, "0" * 32 + ".jpg") is None
