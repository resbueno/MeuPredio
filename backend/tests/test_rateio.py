from __future__ import annotations

from decimal import Decimal

from app.models.enums import RoleEnum
from app.models.log_auditoria import LogAuditoria
from app.models.predio import Predio
from app.models.usuario import Usuario
from tests.utils import auth_header, make_predio, make_unidade, make_user


def _admin_com_predio(db_session, *, email: str) -> tuple[Usuario, Predio]:
    admin = make_user(db_session, email=email, role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    return admin, predio


def _criar_despesa(client, admin, predio, *, valor: str, descricao: str = "Despesa rateio") -> dict:
    return client.post(
        "/despesas",
        json={
            "descricao": descricao,
            "categoria": "outros",
            "valor": valor,
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()


def test_ratear_igualmente_distribui_centavos_sem_perda(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.r1@test.local")
    make_unidade(db_session, predio, bloco="A", numero="1")
    make_unidade(db_session, predio, bloco="A", numero="2")
    make_unidade(db_session, predio, bloco="A", numero="3")
    despesa = _criar_despesa(client, admin, predio, valor="100.00")

    resposta = client.post(
        f"/despesas/{despesa['id']}/ratear", json={"criterio": "igual"}, headers=auth_header(admin)
    )
    assert resposta.status_code == 200
    body = resposta.json()
    itens = body["itens_rateio"]
    assert len(itens) == 3
    assert body["rateado_em"] is not None

    soma = sum(Decimal(item["valor"]) for item in itens)
    assert soma == Decimal("100.00")
    # Nenhuma unidade "perde" mais de 1 centavo de diferenca para outra.
    valores = sorted(Decimal(item["valor"]) for item in itens)
    assert valores[-1] - valores[0] <= Decimal("0.01")


def test_ratear_por_fracao_ideal_e_proporcional(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.r2@test.local")
    u1 = make_unidade(db_session, predio, bloco="A", numero="1", fracao_ideal=Decimal(50))
    u2 = make_unidade(db_session, predio, bloco="A", numero="2", fracao_ideal=Decimal(30))
    u3 = make_unidade(db_session, predio, bloco="A", numero="3", fracao_ideal=Decimal(20))
    despesa = _criar_despesa(client, admin, predio, valor="1000.00")

    resposta = client.post(
        f"/despesas/{despesa['id']}/ratear",
        json={"criterio": "fracao_ideal"},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 200
    itens = {item["unidade_id"]: Decimal(item["valor"]) for item in resposta.json()["itens_rateio"]}
    assert itens[u1.id] == Decimal("500.00")
    assert itens[u2.id] == Decimal("300.00")
    assert itens[u3.id] == Decimal("200.00")

    log = (
        db_session.query(LogAuditoria)
        .filter(LogAuditoria.entidade == "despesas_lancamentos", LogAuditoria.acao == "RATEIO")
        .one_or_none()
    )
    assert log is not None
    assert log.dados_depois["criterio"] == "fracao_ideal"


def test_ratear_por_fracao_ideal_sem_fracao_definida_retorna_422(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.r3@test.local")
    make_unidade(db_session, predio, bloco="A", numero="1", fracao_ideal=Decimal(50))
    make_unidade(db_session, predio, bloco="A", numero="2")  # sem fracao_ideal
    despesa = _criar_despesa(client, admin, predio, valor="100.00")

    resposta = client.post(
        f"/despesas/{despesa['id']}/ratear",
        json={"criterio": "fracao_ideal"},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 422


def test_ratear_sem_unidades_ativas_retorna_409(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.r4@test.local")
    despesa = _criar_despesa(client, admin, predio, valor="100.00")

    resposta = client.post(
        f"/despesas/{despesa['id']}/ratear", json={"criterio": "igual"}, headers=auth_header(admin)
    )
    assert resposta.status_code == 409


def test_ratear_despesa_ja_paga_retorna_409(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.r5@test.local")
    make_unidade(db_session, predio)
    despesa = _criar_despesa(client, admin, predio, valor="100.00")
    client.post(f"/despesas/{despesa['id']}/pagar", json={}, headers=auth_header(admin))

    resposta = client.post(
        f"/despesas/{despesa['id']}/ratear", json={"criterio": "igual"}, headers=auth_header(admin)
    )
    assert resposta.status_code == 409


def test_ratear_de_novo_substitui_itens_anteriores(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.r6@test.local")
    make_unidade(db_session, predio, bloco="A", numero="1", fracao_ideal=Decimal(1))
    make_unidade(db_session, predio, bloco="A", numero="2", fracao_ideal=Decimal(1))
    despesa = _criar_despesa(client, admin, predio, valor="100.00")

    client.post(f"/despesas/{despesa['id']}/ratear", json={"criterio": "igual"}, headers=auth_header(admin))
    segunda = client.post(
        f"/despesas/{despesa['id']}/ratear",
        json={"criterio": "fracao_ideal"},
        headers=auth_header(admin),
    )
    itens = segunda.json()["itens_rateio"]
    assert len(itens) == 2
    assert all(item["criterio"] == "fracao_ideal" for item in itens)


def test_morador_nao_pode_ratear(client, db_session):
    morador = make_user(db_session, email="morador.r1@test.local", role=RoleEnum.MORADOR)
    despesa = _criar_despesa(
        client,
        make_user(db_session, email="admin.r7@test.local", role=RoleEnum.ADMINISTRADOR),
        morador.predio,
        valor="100.00",
    )
    resposta = client.post(
        f"/despesas/{despesa['id']}/ratear", json={"criterio": "igual"}, headers=auth_header(morador)
    )
    assert resposta.status_code == 403
