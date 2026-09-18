from __future__ import annotations

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_unidade, make_user


def test_zelador_registra_entrega_e_notifica_unidade(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    zelador = make_user(db_session, email="zelador.en1@test.local", role=RoleEnum.ZELADOR, predio=predio)
    morador = make_user(
        db_session, email="morador.en1@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )

    resposta = client.post(
        "/entregas",
        json={"unidade_id": unidade.id, "descricao": "Pacote Amazon", "localizacao": "Portaria"},
        headers=auth_header(zelador),
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["retirada_em"] is None

    notificacoes = client.get("/notificacoes", headers=auth_header(morador)).json()
    assert len(notificacoes) == 1
    assert notificacoes[0]["tipo"] == "entrega"
    assert notificacoes[0]["referencia_id"] == corpo["id"]

    # Quem registrou nao notifica a si mesmo.
    assert client.get("/notificacoes", headers=auth_header(zelador)).json() == []


def test_morador_nao_registra_entrega(client, db_session):
    morador = make_user(db_session, email="morador.en2@test.local", role=RoleEnum.MORADOR)
    resposta = client.post(
        "/entregas",
        json={"unidade_id": morador.unidades[0].id, "descricao": "X", "localizacao": "Y"},
        headers=auth_header(morador),
    )
    assert resposta.status_code == 403


def test_morador_so_ve_entrega_da_propria_unidade(client, db_session):
    predio = make_predio(db_session)
    unidade1 = make_unidade(db_session, predio, bloco="A", numero="101")
    unidade2 = make_unidade(db_session, predio, bloco="A", numero="102")
    sindico = make_user(db_session, email="sindico.en1@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador1 = make_user(
        db_session, email="morador.en3@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade1]
    )
    morador2 = make_user(
        db_session, email="morador.en4@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade2]
    )

    entrega = client.post(
        "/entregas",
        json={"unidade_id": unidade1.id, "descricao": "Caixa", "localizacao": "Portaria"},
        headers=auth_header(sindico),
    ).json()

    assert len(client.get("/entregas", headers=auth_header(morador1)).json()) == 1
    assert client.get("/entregas", headers=auth_header(morador2)).json() == []
    assert len(client.get("/entregas", headers=auth_header(sindico)).json()) == 1

    retirada = client.post(f"/entregas/{entrega['id']}/retirar", headers=auth_header(morador1))
    assert retirada.status_code == 200
    assert retirada.json()["retirada_por"] == morador1.id
    assert retirada.json()["retirada_em"] is not None

    conflito = client.post(f"/entregas/{entrega['id']}/retirar", headers=auth_header(sindico))
    assert conflito.status_code == 409
