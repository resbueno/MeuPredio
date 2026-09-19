from __future__ import annotations

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_unidade, make_user


def test_zelador_registra_visitante(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    zelador = make_user(db_session, email="zelador.vi1@test.local", role=RoleEnum.ZELADOR, predio=predio)

    resposta = client.post(
        "/visitantes",
        json={
            "unidade_id": unidade.id,
            "nome_completo": "Fulano de Tal",
            "tipo_documento": "rg",
            "numero_documento": "12.345.678-9",
        },
        headers=auth_header(zelador),
    )
    assert resposta.status_code == 201
    assert resposta.json()["nome_completo"] == "Fulano de Tal"


def test_documento_nao_informado_rejeita_numero(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    zelador = make_user(db_session, email="zelador.vi2@test.local", role=RoleEnum.ZELADOR, predio=predio)

    resposta = client.post(
        "/visitantes",
        json={
            "unidade_id": unidade.id,
            "nome_completo": "Fulano",
            "tipo_documento": "nao_informado",
            "numero_documento": "123",
        },
        headers=auth_header(zelador),
    )
    assert resposta.status_code == 422


def test_documento_rg_exige_numero(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    zelador = make_user(db_session, email="zelador.vi3@test.local", role=RoleEnum.ZELADOR, predio=predio)

    resposta = client.post(
        "/visitantes",
        json={"unidade_id": unidade.id, "nome_completo": "Fulano", "tipo_documento": "cpf"},
        headers=auth_header(zelador),
    )
    assert resposta.status_code == 422


def test_documento_nao_informado_aceito_sem_numero(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    zelador = make_user(db_session, email="zelador.vi4@test.local", role=RoleEnum.ZELADOR, predio=predio)

    resposta = client.post(
        "/visitantes",
        json={"unidade_id": unidade.id, "nome_completo": "Fulano", "tipo_documento": "nao_informado"},
        headers=auth_header(zelador),
    )
    assert resposta.status_code == 201


def test_morador_nao_registra_nem_ve_visitantes(client, db_session):
    morador = make_user(db_session, email="morador.vi1@test.local", role=RoleEnum.MORADOR)

    criar = client.post(
        "/visitantes",
        json={
            "unidade_id": morador.unidades[0].id,
            "nome_completo": "Fulano",
            "tipo_documento": "nao_informado",
        },
        headers=auth_header(morador),
    )
    assert criar.status_code == 403

    listar = client.get("/visitantes", headers=auth_header(morador))
    assert listar.status_code == 403


def test_sindico_ve_apenas_visitantes_do_proprio_predio(client, db_session):
    predio1 = make_predio(db_session)
    predio2 = make_predio(db_session)
    unidade1 = make_unidade(db_session, predio1)
    unidade2 = make_unidade(db_session, predio2)
    zelador1 = make_user(db_session, email="zelador.vi5@test.local", role=RoleEnum.ZELADOR, predio=predio1)
    sindico1 = make_user(db_session, email="sindico.vi1@test.local", role=RoleEnum.SINDICO, predio=predio1)
    sindico2 = make_user(db_session, email="sindico.vi2@test.local", role=RoleEnum.SINDICO, predio=predio2)

    client.post(
        "/visitantes",
        json={"unidade_id": unidade1.id, "nome_completo": "Visitante 1", "tipo_documento": "nao_informado"},
        headers=auth_header(zelador1),
    )
    client.post(
        "/visitantes",
        json={"unidade_id": unidade2.id, "nome_completo": "Visitante 2", "tipo_documento": "nao_informado"},
        headers=auth_header(sindico2),
    )

    assert len(client.get("/visitantes", headers=auth_header(sindico1)).json()) == 1
    assert len(client.get("/visitantes", headers=auth_header(sindico2)).json()) == 1
