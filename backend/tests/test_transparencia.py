from __future__ import annotations

from app.models.enums import RoleEnum
from app.models.predio import Predio
from app.models.usuario import Usuario
from tests.utils import auth_header, make_predio, make_user


def _admin_com_predio(db_session, *, email: str) -> tuple[Usuario, Predio]:
    admin = make_user(db_session, email=email, role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    return admin, predio


def _criar_despesa(client, admin: Usuario, predio: Predio, **overrides) -> dict:
    payload = {
        "descricao": "Conta",
        "categoria": "agua",
        "valor": "100",
        "data_vencimento": "2026-05-10",
        "predio_id": predio.id,
        **overrides,
    }
    return client.post("/despesas", json=payload, headers=auth_header(admin)).json()


def test_morador_ve_despesas_do_proprio_predio(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.t1@test.local")
    morador = make_user(db_session, email="morador.t1@test.local", role=RoleEnum.MORADOR, predio=predio)
    _criar_despesa(client, admin, predio)

    resposta = client.get("/transparencia/despesas", headers=auth_header(morador))
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1
    # observacoes nunca vaza no recorte publico do Portal da Transparencia.
    assert "observacoes" not in resposta.json()[0]


def test_morador_nao_ve_despesas_de_outro_predio(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.t2@test.local")
    outro_predio = make_predio(db_session)
    outro_admin = make_user(db_session, email="admin.t2b@test.local", role=RoleEnum.ADMINISTRADOR)
    morador = make_user(db_session, email="morador.t2@test.local", role=RoleEnum.MORADOR, predio=predio)

    _criar_despesa(client, outro_admin, outro_predio)

    resposta = client.get("/transparencia/despesas", headers=auth_header(morador))
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_administrador_sem_predio_id_retorna_422(client, db_session):
    admin, _predio = _admin_com_predio(db_session, email="admin.t3@test.local")
    resposta = client.get("/transparencia/despesas", headers=auth_header(admin))
    assert resposta.status_code == 422


def test_balancete_agrega_por_status_e_categoria(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.t4@test.local")
    morador = make_user(db_session, email="morador.t4@test.local", role=RoleEnum.MORADOR, predio=predio)

    paga = _criar_despesa(client, admin, predio, descricao="Agua", categoria="agua", valor="100")
    client.post(f"/despesas/{paga['id']}/pagar", json={}, headers=auth_header(admin))
    _criar_despesa(client, admin, predio, descricao="Luz", categoria="luz", valor="50")

    resposta = client.get(
        "/transparencia/balancete",
        params={"ano": 2026, "mes": 5},
        headers=auth_header(morador),
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total_pago"] == "100.00"
    assert corpo["total_pendente"] == "50.00"
    assert corpo["total_geral"] == "150.00"
    categorias = {item["categoria"]: item["total"] for item in corpo["por_categoria"]}
    assert categorias == {"agua": "100.00", "luz": "50.00"}


def test_balancete_ignora_lancamento_fora_do_periodo(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.t5@test.local")
    morador = make_user(db_session, email="morador.t5@test.local", role=RoleEnum.MORADOR, predio=predio)
    _criar_despesa(client, admin, predio, data_vencimento="2026-01-10")

    resposta = client.get(
        "/transparencia/balancete",
        params={"ano": 2026, "mes": 5},
        headers=auth_header(morador),
    )
    assert resposta.json()["total_geral"] == "0.00"


def test_zelador_pode_ver_documento_de_despesa_do_proprio_predio(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.t6@test.local")
    zelador = make_user(db_session, email="zelador.t6@test.local", role=RoleEnum.ZELADOR, predio=predio)

    resposta = client.get(
        f"/despesas/documentos/{predio.id}/arquivo-inexistente.pdf", headers=auth_header(zelador)
    )
    # Nao e mais 403 (papel bloqueado antes de chegar aqui) - passa a guarda
    # de RBAC e cai em 404 so porque o arquivo em si nao existe.
    assert resposta.status_code == 404
