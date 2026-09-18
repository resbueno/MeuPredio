from __future__ import annotations

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_user


def test_morador_registra_ocorrencia(client, db_session):
    morador = make_user(db_session, email="morador.oc1@test.local", role=RoleEnum.MORADOR)
    resposta = client.post(
        "/ocorrencias",
        json={"titulo": "Vazamento na garagem", "descricao": "Agua acumulando perto da vaga 5."},
        headers=auth_header(morador),
    )
    assert resposta.status_code == 201
    assert resposta.json()["editado_em"] is None


def test_morador_nao_ve_ocorrencia_de_outro(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.oc2@test.local", role=RoleEnum.MORADOR, predio=predio)
    outro = make_user(db_session, email="morador.oc3@test.local", role=RoleEnum.MORADOR, predio=predio)

    criado = client.post(
        "/ocorrencias", json={"titulo": "XX", "descricao": "YY"}, headers=auth_header(autor)
    ).json()

    assert client.get(f"/ocorrencias/{criado['id']}", headers=auth_header(outro)).status_code == 404
    assert client.get("/ocorrencias", headers=auth_header(outro)).json() == []


def test_sindico_ve_todas_e_edita_marcando_editado(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.oc4@test.local", role=RoleEnum.MORADOR, predio=predio)
    sindico = make_user(db_session, email="sindico.oc1@test.local", role=RoleEnum.SINDICO, predio=predio)

    criado = client.post(
        "/ocorrencias", json={"titulo": "XX", "descricao": "YY"}, headers=auth_header(autor)
    ).json()

    assert client.get(f"/ocorrencias/{criado['id']}", headers=auth_header(sindico)).status_code == 200

    editado = client.patch(
        f"/ocorrencias/{criado['id']}", json={"descricao": "Complemento do sindico"}, headers=auth_header(sindico)
    )
    assert editado.status_code == 200
    assert editado.json()["editado_em"] is not None
    assert editado.json()["editado_por"] == sindico.id
    assert editado.json()["descricao"] == "Complemento do sindico"


def test_autor_nao_pode_editar_propria_ocorrencia(client, db_session):
    autor = make_user(db_session, email="morador.oc5@test.local", role=RoleEnum.MORADOR)
    criado = client.post(
        "/ocorrencias", json={"titulo": "XX", "descricao": "YY"}, headers=auth_header(autor)
    ).json()

    resposta = client.patch(
        f"/ocorrencias/{criado['id']}", json={"titulo": "Editado"}, headers=auth_header(autor)
    )
    assert resposta.status_code == 403
