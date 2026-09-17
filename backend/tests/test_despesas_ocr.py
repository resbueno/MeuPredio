from __future__ import annotations

from decimal import Decimal

from app.core.crypto import encrypt_secret
from app.core.groq_ocr import ExtracaoBoleto, GroqIndisponivelError
from app.models.enums import RoleEnum
from app.models.predio import Predio
from app.models.usuario import Usuario
from tests.utils import auth_header, make_predio, make_user


def _admin_com_predio_e_integracao(db_session, *, email: str) -> tuple[Usuario, Predio]:
    admin = make_user(db_session, email=email, role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    predio.groq_api_key_cifrada = encrypt_secret("gsk_chave-de-teste")
    db_session.add(predio)
    db_session.commit()
    db_session.refresh(predio)
    return admin, predio


def _extracao_fake(**overrides) -> ExtracaoBoleto:
    base = {
        "fornecedor_nome": "Companhia de Agua",
        "fornecedor_documento": "12345678000199",
        "valor": Decimal("150.75"),
        "data_vencimento": None,
        "linha_digitavel": "12345 67890",
        "descricao_sugerida": "Conta de agua",
        "categoria_sugerida": "agua",
    }
    base.update(overrides)
    return ExtracaoBoleto(**base)


def test_extrair_boleto_sem_integracao_configurada_retorna_409(client, db_session):
    admin = make_user(db_session, email="admin.ocrd1@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)

    resposta = client.post(
        "/despesas/ocr/extrair",
        files={"arquivo": ("boleto.jpg", b"fake-bytes", "image/jpeg")},
        data={"predio_id": str(predio.id)},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 409


def test_extrair_boleto_com_sucesso(client, db_session, monkeypatch):
    admin, predio = _admin_com_predio_e_integracao(db_session, email="admin.ocrd2@test.local")

    chamadas = []

    def _fake_extrair(*, api_key, conteudo, mime_type):
        chamadas.append((api_key, conteudo, mime_type))
        return _extracao_fake()

    monkeypatch.setattr("app.routers.despesas.extrair_dados_boleto", _fake_extrair)

    resposta = client.post(
        "/despesas/ocr/extrair",
        files={"arquivo": ("boleto.jpg", b"fake-bytes", "image/jpeg")},
        data={"predio_id": str(predio.id)},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 200
    body = resposta.json()
    assert body["fornecedor_nome"] == "Companhia de Agua"
    assert body["valor"] == "150.75"
    assert body["documento_url"].startswith(f"despesas/documentos/{predio.id}/")

    assert len(chamadas) == 1
    api_key_usada, conteudo_recebido, mime_recebido = chamadas[0]
    assert api_key_usada == "gsk_chave-de-teste"
    assert conteudo_recebido == b"fake-bytes"
    assert mime_recebido == "image/jpeg"


def test_extrair_boleto_pdf_e_convertido_para_imagem_antes_do_groq(client, db_session, monkeypatch):
    import pymupdf

    admin, predio = _admin_com_predio_e_integracao(db_session, email="admin.ocrd7@test.local")

    documento_pdf = pymupdf.open()
    pagina = documento_pdf.new_page()
    pagina.insert_text((72, 72), "Boleto de teste - R$ 200,00")
    pdf_bytes = documento_pdf.tobytes()

    chamadas = []

    def _fake_extrair(*, api_key, conteudo, mime_type):
        chamadas.append((conteudo, mime_type))
        return _extracao_fake()

    monkeypatch.setattr("app.routers.despesas.extrair_dados_boleto", _fake_extrair)

    resposta = client.post(
        "/despesas/ocr/extrair",
        files={"arquivo": ("boleto.pdf", pdf_bytes, "application/pdf")},
        data={"predio_id": str(predio.id)},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 200
    assert resposta.json()["documento_url"].endswith(".pdf")

    assert len(chamadas) == 1
    conteudo_enviado, mime_enviado = chamadas[0]
    assert mime_enviado == "image/png"
    assert conteudo_enviado.startswith(b"\x89PNG\r\n\x1a\n")
    assert conteudo_enviado != pdf_bytes


def test_extrair_boleto_pdf_corrompido_retorna_422(client, db_session):
    admin, predio = _admin_com_predio_e_integracao(db_session, email="admin.ocrd8@test.local")
    resposta = client.post(
        "/despesas/ocr/extrair",
        files={"arquivo": ("boleto.pdf", b"nao e um pdf valido", "application/pdf")},
        data={"predio_id": str(predio.id)},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 422


def test_extrair_boleto_tipo_arquivo_invalido_retorna_422(client, db_session):
    admin, predio = _admin_com_predio_e_integracao(db_session, email="admin.ocrd3@test.local")
    resposta = client.post(
        "/despesas/ocr/extrair",
        files={"arquivo": ("boleto.txt", b"nao e imagem", "text/plain")},
        data={"predio_id": str(predio.id)},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 422


def test_extrair_boleto_erro_groq_retorna_502(client, db_session, monkeypatch):
    admin, predio = _admin_com_predio_e_integracao(db_session, email="admin.ocrd4@test.local")

    def _fake_extrair(*, api_key, conteudo, mime_type):
        raise GroqIndisponivelError("falha simulada")

    monkeypatch.setattr("app.routers.despesas.extrair_dados_boleto", _fake_extrair)

    resposta = client.post(
        "/despesas/ocr/extrair",
        files={"arquivo": ("boleto.jpg", b"fake-bytes", "image/jpeg")},
        data={"predio_id": str(predio.id)},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 502


def test_morador_nao_pode_extrair_boleto(client, db_session):
    morador = make_user(db_session, email="morador.ocrd1@test.local", role=RoleEnum.MORADOR)
    resposta = client.post(
        "/despesas/ocr/extrair",
        files={"arquivo": ("boleto.jpg", b"fake-bytes", "image/jpeg")},
        headers=auth_header(morador),
    )
    assert resposta.status_code == 403


def test_obter_documento_isolamento_multi_tenant(client, db_session, monkeypatch):
    admin, predio = _admin_com_predio_e_integracao(db_session, email="admin.ocrd5@test.local")
    monkeypatch.setattr(
        "app.routers.despesas.extrair_dados_boleto", lambda **kwargs: _extracao_fake()
    )
    extraido = client.post(
        "/despesas/ocr/extrair",
        files={"arquivo": ("boleto.jpg", b"fake-bytes", "image/jpeg")},
        data={"predio_id": str(predio.id)},
        headers=auth_header(admin),
    ).json()
    documento_url = extraido["documento_url"]

    resposta_admin = client.get(f"/{documento_url}", headers=auth_header(admin))
    assert resposta_admin.status_code == 200
    assert resposta_admin.content == b"fake-bytes"

    sindico_de_outro_predio = make_user(
        db_session, email="sindico.ocrd1@test.local", role=RoleEnum.SINDICO
    )
    resposta_alheia = client.get(f"/{documento_url}", headers=auth_header(sindico_de_outro_predio))
    assert resposta_alheia.status_code == 404


def test_obter_documento_inexistente_retorna_404(client, db_session):
    admin = make_user(db_session, email="admin.ocrd6@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    resposta = client.get(
        f"/despesas/documentos/{predio.id}/{'0' * 32}.jpg", headers=auth_header(admin)
    )
    assert resposta.status_code == 404
