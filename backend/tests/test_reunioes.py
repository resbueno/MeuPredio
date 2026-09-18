from __future__ import annotations

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_unidade, make_user


def _payload_reuniao(**overrides) -> dict:
    return {
        "tipo": "ordinaria",
        "titulo": "Assembleia Geral Ordinária",
        "data_hora": "2026-12-01T19:00:00-03:00",
        "local": "Salão de festas",
        "pauta": "1. Prestação de contas\n2. Eleição de síndico",
        **overrides,
    }


def test_sindico_convoca_reuniao(client, db_session):
    sindico = make_user(db_session, email="sindico.rn1@test.local", role=RoleEnum.SINDICO)
    resposta = client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(sindico))
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "convocada"
    assert corpo["ata"] is None


def test_morador_nao_pode_convocar_reuniao(client, db_session):
    morador = make_user(db_session, email="morador.rn1@test.local", role=RoleEnum.MORADOR)
    resposta = client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(morador))
    assert resposta.status_code == 403


def test_morador_ve_convocacao_do_proprio_predio(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.rn2@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(db_session, email="morador.rn2@test.local", role=RoleEnum.MORADOR, predio=predio)

    client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(sindico))

    resposta = client.get("/reunioes", headers=auth_header(morador))
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


def test_morador_nao_ve_reuniao_de_outro_predio(client, db_session):
    sindico = make_user(db_session, email="sindico.rn3@test.local", role=RoleEnum.SINDICO)
    outro_predio = make_predio(db_session)
    morador = make_user(
        db_session, email="morador.rn3@test.local", role=RoleEnum.MORADOR, predio=outro_predio
    )
    client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(sindico))

    resposta = client.get("/reunioes", headers=auth_header(morador))
    assert resposta.json() == []


def test_morador_confirma_presenca_da_propria_unidade(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.rn4@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session, email="morador.rn4@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )
    criada = client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(sindico)).json()

    resposta = client.post(
        f"/reunioes/{criada['id']}/presenca",
        json={"unidade_id": unidade.id},
        headers=auth_header(morador),
    )
    assert resposta.status_code == 201

    duplicada = client.post(
        f"/reunioes/{criada['id']}/presenca",
        json={"unidade_id": unidade.id},
        headers=auth_header(morador),
    )
    assert duplicada.status_code == 409


def test_morador_nao_confirma_presenca_de_unidade_alheia(client, db_session):
    predio = make_predio(db_session)
    unidade_alheia = make_unidade(db_session, predio, bloco="B", numero="2")
    sindico = make_user(db_session, email="sindico.rn5@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(db_session, email="morador.rn5@test.local", role=RoleEnum.MORADOR, predio=predio)
    criada = client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(sindico)).json()

    resposta = client.post(
        f"/reunioes/{criada['id']}/presenca",
        json={"unidade_id": unidade_alheia.id},
        headers=auth_header(morador),
    )
    assert resposta.status_code == 403


def test_gestao_confirma_presenca_de_qualquer_unidade(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.rn6@test.local", role=RoleEnum.SINDICO, predio=predio)
    criada = client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(sindico)).json()

    resposta = client.post(
        f"/reunioes/{criada['id']}/presenca",
        json={"unidade_id": unidade.id},
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 201


def test_registrar_ata_fecha_reuniao_e_bloqueia_novas_presencas(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.rn7@test.local", role=RoleEnum.SINDICO, predio=predio)
    criada = client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(sindico)).json()

    ata = client.post(
        f"/reunioes/{criada['id']}/ata",
        json={"ata": "Reunião realizada, contas aprovadas por unanimidade."},
        headers=auth_header(sindico),
    )
    assert ata.status_code == 200
    assert ata.json()["status"] == "realizada"
    assert ata.json()["ata_registrada_em"] is not None

    presenca_apos_ata = client.post(
        f"/reunioes/{criada['id']}/presenca",
        json={"unidade_id": unidade.id},
        headers=auth_header(sindico),
    )
    assert presenca_apos_ata.status_code == 409

    edicao_apos_ata = client.patch(
        f"/reunioes/{criada['id']}", json={"titulo": "Outro título"}, headers=auth_header(sindico)
    )
    assert edicao_apos_ata.status_code == 409


def test_cancelar_reuniao(client, db_session):
    sindico = make_user(db_session, email="sindico.rn8@test.local", role=RoleEnum.SINDICO)
    criada = client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(sindico)).json()

    resposta = client.post(f"/reunioes/{criada['id']}/cancelar", headers=auth_header(sindico))
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "cancelada"


def test_gestao_remove_presenca_registrada_por_engano(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.rn9@test.local", role=RoleEnum.SINDICO, predio=predio)
    criada = client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(sindico)).json()
    client.post(
        f"/reunioes/{criada['id']}/presenca",
        json={"unidade_id": unidade.id},
        headers=auth_header(sindico),
    )

    resposta = client.delete(
        f"/reunioes/{criada['id']}/presenca/{unidade.id}", headers=auth_header(sindico)
    )
    assert resposta.status_code == 204

    refeita = client.post(
        f"/reunioes/{criada['id']}/presenca",
        json={"unidade_id": unidade.id},
        headers=auth_header(sindico),
    )
    assert refeita.status_code == 201


def test_administrador_precisa_informar_predio_id(client, db_session):
    admin = make_user(db_session, email="admin.rn1@test.local", role=RoleEnum.ADMINISTRADOR)
    resposta = client.post("/reunioes", json=_payload_reuniao(), headers=auth_header(admin))
    assert resposta.status_code == 422
