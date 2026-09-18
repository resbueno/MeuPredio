from __future__ import annotations

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_user


def test_sindico_publica_aviso_condominio(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.am1@test.local", role=RoleEnum.SINDICO, predio=predio)

    resposta = client.post(
        "/avisos-mural",
        json={"tipo": "condominio", "titulo": "Manutencao do elevador", "descricao": "Dia 20, das 8h as 12h."},
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 201
    assert resposta.json()["tipo"] == "condominio"


def test_morador_nao_pode_publicar_aviso_condominio(client, db_session):
    morador = make_user(db_session, email="morador.am1@test.local", role=RoleEnum.MORADOR)
    resposta = client.post(
        "/avisos-mural",
        json={"tipo": "condominio", "titulo": "XX", "descricao": "YY"},
        headers=auth_header(morador),
    )
    assert resposta.status_code == 403


def test_morador_publica_anuncio_e_so_ele_edita(client, db_session):
    predio = make_predio(db_session)
    morador = make_user(db_session, email="morador.am2@test.local", role=RoleEnum.MORADOR, predio=predio)
    outro = make_user(db_session, email="morador.am3@test.local", role=RoleEnum.MORADOR, predio=predio)

    criado = client.post(
        "/avisos-mural",
        json={"tipo": "anuncio", "titulo": "Sofa usado", "descricao": "Bom estado", "preco": "300"},
        headers=auth_header(morador),
    ).json()

    falha = client.patch(
        f"/avisos-mural/{criado['id']}", json={"titulo": "Sofa novo"}, headers=auth_header(outro)
    )
    assert falha.status_code == 403

    sucesso = client.patch(
        f"/avisos-mural/{criado['id']}", json={"titulo": "Sofa novo"}, headers=auth_header(morador)
    )
    assert sucesso.status_code == 200
    assert sucesso.json()["titulo"] == "Sofa novo"


def test_sindico_remove_anuncio_de_outro_mas_morador_nao(client, db_session):
    predio = make_predio(db_session)
    morador = make_user(db_session, email="morador.am4@test.local", role=RoleEnum.MORADOR, predio=predio)
    outro_morador = make_user(db_session, email="morador.am5@test.local", role=RoleEnum.MORADOR, predio=predio)
    sindico = make_user(db_session, email="sindico.am2@test.local", role=RoleEnum.SINDICO, predio=predio)

    criado = client.post(
        "/avisos-mural",
        json={"tipo": "anuncio", "titulo": "Bike", "descricao": "Aro 29"},
        headers=auth_header(morador),
    ).json()

    falha = client.delete(f"/avisos-mural/{criado['id']}", headers=auth_header(outro_morador))
    assert falha.status_code == 403

    sucesso = client.delete(f"/avisos-mural/{criado['id']}", headers=auth_header(sindico))
    assert sucesso.status_code == 204


def test_listagem_separa_por_tipo(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.am3@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(db_session, email="morador.am6@test.local", role=RoleEnum.MORADOR, predio=predio)

    client.post(
        "/avisos-mural",
        json={"tipo": "condominio", "titulo": "Assembleia", "descricao": "Dia 5"},
        headers=auth_header(sindico),
    )
    client.post(
        "/avisos-mural",
        json={"tipo": "anuncio", "titulo": "Carro", "descricao": "A venda"},
        headers=auth_header(morador),
    )

    somente_condominio = client.get(
        "/avisos-mural", params={"tipo": "condominio"}, headers=auth_header(morador)
    ).json()
    assert len(somente_condominio) == 1
    assert somente_condominio[0]["tipo"] == "condominio"

    todos = client.get("/avisos-mural", headers=auth_header(morador)).json()
    assert len(todos) == 2
