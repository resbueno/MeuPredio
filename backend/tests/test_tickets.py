from __future__ import annotations

from app.models.enums import RoleEnum
from app.models.predio import Predio
from app.models.usuario import Usuario
from tests.utils import auth_header, make_predio, make_unidade, make_user


def _admin_com_predio(db_session, *, email: str) -> tuple[Usuario, Predio]:
    admin = make_user(db_session, email=email, role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    return admin, predio


def _payload_ticket(**overrides) -> dict:
    return {
        "titulo": "Vazamento no teto da garagem",
        "descricao": "Agua escorrendo perto da vaga 12.",
        "categoria": "manutencao",
        "prioridade": "alta",
        **overrides,
    }


def test_criar_ticket_sem_autenticacao_retorna_401(client):
    response = client.post("/tickets", json=_payload_ticket())
    assert response.status_code == 401


def test_morador_cria_ticket_com_sucesso(client, db_session):
    morador = make_user(db_session, email="morador.tk1@test.local", role=RoleEnum.MORADOR)
    resposta = client.post("/tickets", json=_payload_ticket(), headers=auth_header(morador))
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "aberto"
    assert corpo["prazo_sla"] is not None
    assert corpo["esta_atrasado"] is False
    assert corpo["created_by"] == morador.id
    assert corpo["comentarios"] == []


def test_administrador_precisa_informar_predio_id(client, db_session):
    admin, _predio = _admin_com_predio(db_session, email="admin.tk1@test.local")
    resposta = client.post("/tickets", json=_payload_ticket(), headers=auth_header(admin))
    assert resposta.status_code == 422


def test_unidade_de_outro_predio_retorna_404(client, db_session):
    predio = make_predio(db_session)
    outro_predio = make_predio(db_session)
    morador = make_user(db_session, email="morador.tk2@test.local", role=RoleEnum.MORADOR, predio=predio)
    unidade_alheia = make_unidade(db_session, outro_predio)

    resposta = client.post(
        "/tickets",
        json=_payload_ticket(unidade_id=unidade_alheia.id),
        headers=auth_header(morador),
    )
    assert resposta.status_code == 404


def test_morador_nao_ve_ticket_de_outro_morador(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.tk3@test.local", role=RoleEnum.MORADOR, predio=predio)
    outro = make_user(db_session, email="morador.tk4@test.local", role=RoleEnum.MORADOR, predio=predio)

    criado = client.post("/tickets", json=_payload_ticket(), headers=auth_header(autor)).json()

    resposta = client.get(f"/tickets/{criado['id']}", headers=auth_header(outro))
    assert resposta.status_code == 404

    listagem = client.get("/tickets", headers=auth_header(outro))
    assert listagem.json() == []


def test_gestao_ve_todos_tickets_do_predio(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.tk5@test.local", role=RoleEnum.MORADOR, predio=predio)
    zelador = make_user(db_session, email="zelador.tk1@test.local", role=RoleEnum.ZELADOR, predio=predio)

    criado = client.post("/tickets", json=_payload_ticket(), headers=auth_header(autor)).json()

    resposta = client.get(f"/tickets/{criado['id']}", headers=auth_header(zelador))
    assert resposta.status_code == 200

    listagem = client.get("/tickets", headers=auth_header(zelador))
    assert len(listagem.json()) == 1


def test_zelador_assume_e_resolve_ticket(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.tk6@test.local", role=RoleEnum.MORADOR, predio=predio)
    zelador = make_user(db_session, email="zelador.tk2@test.local", role=RoleEnum.ZELADOR, predio=predio)

    criado = client.post("/tickets", json=_payload_ticket(), headers=auth_header(autor)).json()

    assumido = client.post(
        f"/tickets/{criado['id']}/assumir", json={}, headers=auth_header(zelador)
    )
    assert assumido.status_code == 200
    assert assumido.json()["status"] == "em_andamento"
    assert assumido.json()["responsavel_id"] == zelador.id

    resolvido = client.post(f"/tickets/{criado['id']}/resolver", headers=auth_header(zelador))
    assert resolvido.status_code == 200
    assert resolvido.json()["status"] == "resolvido"
    assert resolvido.json()["resolvido_em"] is not None


def test_morador_nao_pode_assumir_ticket(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.tk7@test.local", role=RoleEnum.MORADOR, predio=predio)
    criado = client.post("/tickets", json=_payload_ticket(), headers=auth_header(autor)).json()

    resposta = client.post(f"/tickets/{criado['id']}/assumir", json={}, headers=auth_header(autor))
    assert resposta.status_code == 403


def test_assumir_ticket_ja_em_andamento_retorna_409(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.tk8@test.local", role=RoleEnum.MORADOR, predio=predio)
    zelador = make_user(db_session, email="zelador.tk3@test.local", role=RoleEnum.ZELADOR, predio=predio)
    criado = client.post("/tickets", json=_payload_ticket(), headers=auth_header(autor)).json()
    client.post(f"/tickets/{criado['id']}/assumir", json={}, headers=auth_header(zelador))

    resposta = client.post(f"/tickets/{criado['id']}/assumir", json={}, headers=auth_header(zelador))
    assert resposta.status_code == 409


def test_autor_cancela_proprio_ticket(client, db_session):
    autor = make_user(db_session, email="morador.tk9@test.local", role=RoleEnum.MORADOR)
    criado = client.post("/tickets", json=_payload_ticket(), headers=auth_header(autor)).json()

    resposta = client.post(f"/tickets/{criado['id']}/cancelar", headers=auth_header(autor))
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "cancelado"


def test_autor_nao_pode_editar_apos_ticket_assumido(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.tk10@test.local", role=RoleEnum.MORADOR, predio=predio)
    zelador = make_user(db_session, email="zelador.tk4@test.local", role=RoleEnum.ZELADOR, predio=predio)
    criado = client.post("/tickets", json=_payload_ticket(), headers=auth_header(autor)).json()
    client.post(f"/tickets/{criado['id']}/assumir", json={}, headers=auth_header(zelador))

    resposta = client.patch(
        f"/tickets/{criado['id']}", json={"titulo": "Outro titulo"}, headers=auth_header(autor)
    )
    assert resposta.status_code == 409


def test_autor_e_gestao_comentam_ticket(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.tk11@test.local", role=RoleEnum.MORADOR, predio=predio)
    sindico = make_user(db_session, email="sindico.tk1@test.local", role=RoleEnum.SINDICO, predio=predio)
    criado = client.post("/tickets", json=_payload_ticket(), headers=auth_header(autor)).json()

    c1 = client.post(
        f"/tickets/{criado['id']}/comentarios",
        json={"mensagem": "Alguem ja foi ver?"},
        headers=auth_header(autor),
    )
    assert c1.status_code == 201

    c2 = client.post(
        f"/tickets/{criado['id']}/comentarios",
        json={"mensagem": "Ja estamos verificando."},
        headers=auth_header(sindico),
    )
    assert c2.status_code == 201

    detalhe = client.get(f"/tickets/{criado['id']}", headers=auth_header(autor))
    assert len(detalhe.json()["comentarios"]) == 2


def test_morador_nao_comenta_ticket_alheio(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.tk12@test.local", role=RoleEnum.MORADOR, predio=predio)
    outro = make_user(db_session, email="morador.tk13@test.local", role=RoleEnum.MORADOR, predio=predio)
    criado = client.post("/tickets", json=_payload_ticket(), headers=auth_header(autor)).json()

    resposta = client.post(
        f"/tickets/{criado['id']}/comentarios",
        json={"mensagem": "Intrometido"},
        headers=auth_header(outro),
    )
    assert resposta.status_code == 404
