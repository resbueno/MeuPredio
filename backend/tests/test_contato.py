from __future__ import annotations

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_user


def test_enviar_contato_sem_autenticacao(client):
    resposta = client.post(
        "/contato",
        json={"nome": "Fulano Interessado", "email": "fulano@teste.dev", "mensagem": "Quero saber mais."},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Fulano Interessado"
    assert corpo["atendido"] is False


def test_contato_exige_email_valido(client):
    resposta = client.post("/contato", json={"nome": "Fulano", "email": "nao-e-email"})
    assert resposta.status_code == 422


def test_sindico_nao_lista_contatos(client, db_session):
    sindico = make_user(db_session, email="sindico.ct1@test.local", role=RoleEnum.SINDICO)
    client.post("/contato", json={"nome": "Fulano", "email": "fulano2@teste.dev"})
    resposta = client.get("/contato", headers=auth_header(sindico))
    assert resposta.status_code == 403


def test_administrador_lista_e_marca_atendido(client, db_session):
    admin = make_user(db_session, email="admin.ct1@test.dev", role=RoleEnum.ADMINISTRADOR)
    criado = client.post(
        "/contato", json={"nome": "Ciclano", "email": "ciclano@teste.dev"}
    ).json()

    listados = client.get("/contato", headers=auth_header(admin))
    assert listados.status_code == 200
    assert any(c["id"] == criado["id"] for c in listados.json())

    atendido = client.post(f"/contato/{criado['id']}/marcar-atendido", headers=auth_header(admin))
    assert atendido.status_code == 200
    assert atendido.json()["atendido"] is True

    apenas_pendentes = client.get("/contato?apenas_pendentes=true", headers=auth_header(admin)).json()
    assert all(c["id"] != criado["id"] for c in apenas_pendentes)
