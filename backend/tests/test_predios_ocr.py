from __future__ import annotations

from app.core.crypto import decrypt_secret
from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_user


def test_configurar_integracao_ocr_cifra_a_chave_no_banco(client, db_session):
    admin = make_user(db_session, email="admin.ocr1@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)

    resposta = client.put(
        f"/predios/{predio.id}/integracao-ocr",
        json={"groq_api_key": "gsk_chave-de-teste-do-condominio"},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 200
    assert resposta.json() == {"configurado": True}

    db_session.refresh(predio)
    assert predio.groq_api_key_cifrada is not None
    assert "chave-de-teste-do-condominio" not in predio.groq_api_key_cifrada
    assert decrypt_secret(predio.groq_api_key_cifrada) == "gsk_chave-de-teste-do-condominio"


def test_status_comeca_nao_configurado(client, db_session):
    admin = make_user(db_session, email="admin.ocr2@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)

    resposta = client.get(f"/predios/{predio.id}/integracao-ocr", headers=auth_header(admin))
    assert resposta.status_code == 200
    assert resposta.json() == {"configurado": False}


def test_remover_integracao_ocr(client, db_session):
    admin = make_user(db_session, email="admin.ocr3@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    client.put(
        f"/predios/{predio.id}/integracao-ocr",
        json={"groq_api_key": "gsk_outra-chave"},
        headers=auth_header(admin),
    )

    resposta = client.delete(f"/predios/{predio.id}/integracao-ocr", headers=auth_header(admin))
    assert resposta.status_code == 204

    status_final = client.get(f"/predios/{predio.id}/integracao-ocr", headers=auth_header(admin))
    assert status_final.json() == {"configurado": False}


def test_sindico_configura_apenas_o_proprio_predio(client, db_session):
    sindico = make_user(db_session, email="sindico.ocr1@test.local", role=RoleEnum.SINDICO)
    outro_predio = make_predio(db_session)

    resposta = client.put(
        f"/predios/{outro_predio.id}/integracao-ocr",
        json={"groq_api_key": "gsk_chave-nao-autorizada"},
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 403

    resposta_propria = client.put(
        f"/predios/{sindico.predio_id}/integracao-ocr",
        json={"groq_api_key": "gsk_chave-do-proprio-predio"},
        headers=auth_header(sindico),
    )
    assert resposta_propria.status_code == 200


def test_morador_nao_pode_configurar_integracao_ocr(client, db_session):
    morador = make_user(db_session, email="morador.ocr1@test.local", role=RoleEnum.MORADOR)
    resposta = client.put(
        f"/predios/{morador.predio_id}/integracao-ocr",
        json={"groq_api_key": "gsk_chave-qualquer"},
        headers=auth_header(morador),
    )
    assert resposta.status_code == 403


def test_log_de_auditoria_nunca_contem_a_chave_em_texto_plano(client, db_session):
    from app.models.log_auditoria import LogAuditoria

    admin = make_user(db_session, email="admin.ocr4@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    client.put(
        f"/predios/{predio.id}/integracao-ocr",
        json={"groq_api_key": "gsk_segredo-que-nao-pode-vazar-no-log"},
        headers=auth_header(admin),
    )

    log = (
        db_session.query(LogAuditoria)
        .filter(LogAuditoria.entidade == "predios", LogAuditoria.entidade_id == predio.id)
        .order_by(LogAuditoria.id.desc())
        .first()
    )
    assert log is not None
    assert "segredo-que-nao-pode-vazar-no-log" not in str(log.dados_depois)
