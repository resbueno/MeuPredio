from __future__ import annotations

from datetime import date

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_user


def _mes_anterior(dia1: date) -> date:
    if dia1.month == 1:
        return date(dia1.year - 1, 12, 1)
    return date(dia1.year, dia1.month - 1, 1)


# Cenário determinístico independente do dia do mês em que os testes rodam:
# dia_vencimento=1 + data_inicio no primeiro dia do mês PASSADO garante
# sempre exatamente duas competências já vencidas (mês passado e mês atual,
# ambos dia 1) na primeira chamada de geração, nunca mais nem menos.
_DATA_INICIO_2_COMPETENCIAS = _mes_anterior(date.today().replace(day=1))
_MES_ATUAL_DIA_1 = date.today().replace(day=1)


def test_sindico_cria_fornecedor_com_cnpj_razao_social_nome_fantasia(client, db_session):
    sindico = make_user(db_session, email="sindico.fcnpj1@test.local", role=RoleEnum.SINDICO)
    resposta = client.post(
        "/fornecedores",
        json={
            "nome": "Água Cristalina",
            "cnpj": "12.345.678/0001-99",
            "razao_social": "Água Cristalina Distribuidora Ltda",
            "nome_fantasia": "Água Cristalina",
            "categoria": "agua",
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["cnpj"] == "12345678000199"
    assert corpo["razao_social"] == "Água Cristalina Distribuidora Ltda"
    assert corpo["nome_fantasia"] == "Água Cristalina"


def test_cnpj_invalido_rejeitado(client, db_session):
    sindico = make_user(db_session, email="sindico.fcnpj2@test.local", role=RoleEnum.SINDICO)
    resposta = client.post(
        "/fornecedores",
        json={"nome": "Empresa X", "cnpj": "123", "categoria": "outros"},
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 422


def test_sindico_cria_despesa_recorrente(client, db_session):
    sindico = make_user(db_session, email="sindico.dr1@test.local", role=RoleEnum.SINDICO)
    resposta = client.post(
        "/despesas-recorrentes",
        json={
            "descricao": "Conta de água",
            "categoria": "agua",
            "valor": "350.00",
            "dia_vencimento": 10,
            "data_inicio": str(_MES_ATUAL_DIA_1),
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 201
    assert resposta.json()["ativo"] is True
    assert resposta.json()["ultima_geracao"] is None


def test_morador_nao_cria_despesa_recorrente(client, db_session):
    morador = make_user(db_session, email="morador.dr1@test.local", role=RoleEnum.MORADOR)
    resposta = client.post(
        "/despesas-recorrentes",
        json={
            "descricao": "Conta de luz",
            "categoria": "luz",
            "valor": "200.00",
            "dia_vencimento": 5,
            "data_inicio": str(_MES_ATUAL_DIA_1),
        },
        headers=auth_header(morador),
    )
    assert resposta.status_code == 403


def test_dia_vencimento_fora_do_intervalo_rejeitado(client, db_session):
    sindico = make_user(db_session, email="sindico.dr2@test.local", role=RoleEnum.SINDICO)
    resposta = client.post(
        "/despesas-recorrentes",
        json={
            "descricao": "Conta X",
            "categoria": "outros",
            "valor": "10.00",
            "dia_vencimento": 31,
            "data_inicio": str(_MES_ATUAL_DIA_1),
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 422


def test_gerar_pendentes_cria_lancamentos_vencidos_e_e_idempotente(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.dr3@test.local", role=RoleEnum.SINDICO, predio=predio)

    client.post(
        "/despesas-recorrentes",
        json={
            "descricao": "Conta de condomínio - zeladoria",
            "categoria": "servicos",
            "valor": "1200.00",
            "dia_vencimento": 1,
            "data_inicio": str(_DATA_INICIO_2_COMPETENCIAS),
        },
        headers=auth_header(sindico),
    )

    primeira_geracao = client.post(
        "/despesas-recorrentes/gerar-pendentes", headers=auth_header(sindico)
    )
    assert primeira_geracao.status_code == 200
    gerados = primeira_geracao.json()
    assert len(gerados) == 2
    assert {g["data_vencimento"] for g in gerados} == {
        str(_DATA_INICIO_2_COMPETENCIAS),
        str(_MES_ATUAL_DIA_1),
    }
    assert all(g["status"] == "pendente" for g in gerados)

    # Rodar de novo nao duplica (idempotente).
    segunda_geracao = client.post(
        "/despesas-recorrentes/gerar-pendentes", headers=auth_header(sindico)
    )
    assert segunda_geracao.status_code == 200
    assert segunda_geracao.json() == []

    todas_despesas = client.get("/despesas", headers=auth_header(sindico)).json()
    geradas_desta_recorrente = [
        d for d in todas_despesas if d.get("descricao") == "Conta de condomínio - zeladoria"
    ]
    assert len(geradas_desta_recorrente) == 2


def test_desativar_recorrente_impede_geracao(client, db_session):
    sindico = make_user(db_session, email="sindico.dr4@test.local", role=RoleEnum.SINDICO)

    recorrente = client.post(
        "/despesas-recorrentes",
        json={
            "descricao": "Conta de internet",
            "categoria": "internet",
            "valor": "150.00",
            "dia_vencimento": 1,
            "data_inicio": str(_DATA_INICIO_2_COMPETENCIAS),
        },
        headers=auth_header(sindico),
    ).json()

    desativada = client.patch(
        f"/despesas-recorrentes/{recorrente['id']}", json={"ativo": False}, headers=auth_header(sindico)
    )
    assert desativada.status_code == 200
    assert desativada.json()["ativo"] is False

    gerados = client.post("/despesas-recorrentes/gerar-pendentes", headers=auth_header(sindico))
    assert gerados.json() == []
