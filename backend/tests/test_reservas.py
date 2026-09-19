from __future__ import annotations

from datetime import date, timedelta

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_unidade, make_user


def test_sindico_cria_area_e_libera_agenda_por_dias(client, db_session):
    sindico = make_user(db_session, email="sindico.ar1@test.local", role=RoleEnum.SINDICO)

    criada = client.post(
        "/areas-comuns",
        json={"nome": "Salão de festas", "capacidade": 50},
        headers=auth_header(sindico),
    )
    assert criada.status_code == 201
    assert criada.json()["agenda_liberada_ate"] is None

    liberada = client.post(
        f"/areas-comuns/{criada.json()['id']}/liberar-agenda",
        json={"dias": 60},
        headers=auth_header(sindico),
    )
    assert liberada.status_code == 200
    assert liberada.json()["agenda_liberada_ate"] == str(date.today() + timedelta(days=60))


def test_liberar_agenda_com_data_passada_rejeitada(client, db_session):
    sindico = make_user(db_session, email="sindico.ar2@test.local", role=RoleEnum.SINDICO)
    area = client.post("/areas-comuns", json={"nome": "Churrasqueira"}, headers=auth_header(sindico)).json()

    resposta = client.post(
        f"/areas-comuns/{area['id']}/liberar-agenda",
        json={"ate": str(date.today() - timedelta(days=1))},
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 422


def test_morador_nao_cria_area(client, db_session):
    morador = make_user(db_session, email="morador.ar1@test.local", role=RoleEnum.MORADOR)
    resposta = client.post("/areas-comuns", json={"nome": "Piscina"}, headers=auth_header(morador))
    assert resposta.status_code == 403


def test_morador_reserva_dentro_da_agenda_liberada(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.ar3@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session, email="morador.ar2@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )

    area = client.post(
        "/areas-comuns", json={"nome": "Salão de festas"}, headers=auth_header(sindico)
    ).json()
    client.post(f"/areas-comuns/{area['id']}/liberar-agenda", json={"dias": 60}, headers=auth_header(sindico))

    data_reserva = str(date.today() + timedelta(days=10))
    reserva = client.post(
        "/reservas",
        json={"area_comum_id": area["id"], "data": data_reserva},
        headers=auth_header(morador),
    )
    assert reserva.status_code == 201
    assert reserva.json()["unidade_id"] == unidade.id
    assert reserva.json()["status"] == "confirmada"


def test_reserva_fora_da_agenda_liberada_retorna_409(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.ar4@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session, email="morador.ar3@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )

    area = client.post("/areas-comuns", json={"nome": "Salão"}, headers=auth_header(sindico)).json()
    client.post(f"/areas-comuns/{area['id']}/liberar-agenda", json={"dias": 5}, headers=auth_header(sindico))

    data_fora = str(date.today() + timedelta(days=30))
    resposta = client.post(
        "/reservas",
        json={"area_comum_id": area["id"], "data": data_fora},
        headers=auth_header(morador),
    )
    assert resposta.status_code == 409


def test_dupla_reserva_mesma_area_data_retorna_409_e_cancelamento_libera(client, db_session):
    predio = make_predio(db_session)
    unidade1 = make_unidade(db_session, predio, bloco="A", numero="101")
    unidade2 = make_unidade(db_session, predio, bloco="A", numero="102")
    sindico = make_user(db_session, email="sindico.ar5@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador1 = make_user(
        db_session, email="morador.ar4@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade1]
    )
    morador2 = make_user(
        db_session, email="morador.ar5@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade2]
    )

    area = client.post("/areas-comuns", json={"nome": "Salão"}, headers=auth_header(sindico)).json()
    client.post(f"/areas-comuns/{area['id']}/liberar-agenda", json={"dias": 60}, headers=auth_header(sindico))

    data_reserva = str(date.today() + timedelta(days=15))
    primeira = client.post(
        "/reservas", json={"area_comum_id": area["id"], "data": data_reserva}, headers=auth_header(morador1)
    )
    assert primeira.status_code == 201

    segunda = client.post(
        "/reservas", json={"area_comum_id": area["id"], "data": data_reserva}, headers=auth_header(morador2)
    )
    assert segunda.status_code == 409

    cancelar = client.post(
        f"/reservas/{primeira.json()['id']}/cancelar", headers=auth_header(morador1)
    )
    assert cancelar.status_code == 200
    assert cancelar.json()["status"] == "cancelada"

    terceira = client.post(
        "/reservas", json={"area_comum_id": area["id"], "data": data_reserva}, headers=auth_header(morador2)
    )
    assert terceira.status_code == 201


def test_morador_nao_reserva_para_outra_unidade(client, db_session):
    predio = make_predio(db_session)
    unidade1 = make_unidade(db_session, predio, bloco="A", numero="201")
    unidade2 = make_unidade(db_session, predio, bloco="A", numero="202")
    sindico = make_user(db_session, email="sindico.ar6@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador1 = make_user(
        db_session, email="morador.ar6@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade1]
    )

    area = client.post("/areas-comuns", json={"nome": "Salão"}, headers=auth_header(sindico)).json()
    client.post(f"/areas-comuns/{area['id']}/liberar-agenda", json={"dias": 60}, headers=auth_header(sindico))

    resposta = client.post(
        "/reservas",
        json={
            "area_comum_id": area["id"],
            "data": str(date.today() + timedelta(days=5)),
            "unidade_id": unidade2.id,
        },
        headers=auth_header(morador1),
    )
    assert resposta.status_code == 403


def test_morador_so_ve_reservas_da_propria_unidade(client, db_session):
    predio = make_predio(db_session)
    unidade1 = make_unidade(db_session, predio, bloco="B", numero="301")
    unidade2 = make_unidade(db_session, predio, bloco="B", numero="302")
    sindico = make_user(db_session, email="sindico.ar7@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador1 = make_user(
        db_session, email="morador.ar7@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade1]
    )
    morador2 = make_user(
        db_session, email="morador.ar8@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade2]
    )

    area = client.post("/areas-comuns", json={"nome": "Salão"}, headers=auth_header(sindico)).json()
    client.post(f"/areas-comuns/{area['id']}/liberar-agenda", json={"dias": 60}, headers=auth_header(sindico))
    client.post(
        "/reservas",
        json={"area_comum_id": area["id"], "data": str(date.today() + timedelta(days=3))},
        headers=auth_header(morador1),
    )

    assert len(client.get("/reservas", headers=auth_header(morador1)).json()) == 1
    assert client.get("/reservas", headers=auth_header(morador2)).json() == []
    assert len(client.get("/reservas", headers=auth_header(sindico)).json()) == 1
