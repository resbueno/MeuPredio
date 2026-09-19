from __future__ import annotations

from datetime import date

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_unidade, make_user


def _cenario(db_session):
    """Prédio com duas unidades; síndico e zelador vinculados à primeira
    (sem criar unidades extras - o rateio divide entre TODAS as ativas)."""
    predio = make_predio(db_session)
    u1 = make_unidade(db_session, predio, bloco="A", numero="101")
    u2 = make_unidade(db_session, predio, bloco="A", numero="102")
    sindico = make_user(db_session, email="sindico.eq@test.local", role=RoleEnum.SINDICO, predio=predio, unidades=[u1])
    zelador = make_user(db_session, email="zelador.eq@test.local", role=RoleEnum.ZELADOR, predio=predio, unidades=[u1])
    return predio, u1, u2, sindico, zelador


def test_sindico_e_zelador_cadastram_e_veem_funcionarios(client, db_session):
    _, _, _, sindico, zelador = _cenario(db_session)

    criado = client.post(
        "/funcionarios",
        json={"nome_completo": "Antônio Souza", "cargo": "Porteiro", "cpf": "123.456.789-09", "salario": "2100.50"},
        headers=auth_header(zelador),
    )
    assert criado.status_code == 201
    assert criado.json()["cpf"] == "12345678909"
    assert criado.json()["ativo"] is True

    assert len(client.get("/funcionarios", headers=auth_header(sindico)).json()) == 1


def test_morador_e_administrador_nao_acessam_equipe(client, db_session):
    predio, u1, _, _, _ = _cenario(db_session)
    morador = make_user(db_session, email="morador.eq@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[u1])
    admin = make_user(db_session, email="admin.eq@test.dev", role=RoleEnum.ADMINISTRADOR)

    for usuario in (morador, admin):
        assert client.get("/funcionarios", headers=auth_header(usuario)).status_code == 403
        assert client.get("/prestadores-servico", headers=auth_header(usuario)).status_code == 403
        assert client.post(
            "/prestadores-servico",
            json={"nome": "X", "tipo_servico": "Limpeza", "custo_mensal": "10.00"},
            headers=auth_header(usuario),
        ).status_code == 403


def test_funcionarios_isolados_por_predio(client, db_session):
    _, _, _, sindico1, _ = _cenario(db_session)
    sindico2 = make_user(db_session, email="sindico.eq2@test.local", role=RoleEnum.SINDICO)

    criado = client.post(
        "/funcionarios", json={"nome_completo": "Maria Lima", "cargo": "Faxineira"}, headers=auth_header(sindico1)
    ).json()

    assert client.get("/funcionarios", headers=auth_header(sindico2)).json() == []
    assert client.patch(
        f"/funcionarios/{criado['id']}", json={"cargo": "Cargo novo"}, headers=auth_header(sindico2)
    ).status_code == 404


def test_desativar_e_remover_funcionario(client, db_session):
    _, _, _, sindico, _ = _cenario(db_session)
    f = client.post(
        "/funcionarios", json={"nome_completo": "João Reis", "cargo": "Jardineiro"}, headers=auth_header(sindico)
    ).json()

    client.patch(f"/funcionarios/{f['id']}", json={"ativo": False}, headers=auth_header(sindico))
    assert client.get("/funcionarios", headers=auth_header(sindico)).json() == []
    assert len(client.get("/funcionarios?incluir_inativos=true", headers=auth_header(sindico)).json()) == 1

    assert client.delete(f"/funcionarios/{f['id']}", headers=auth_header(sindico)).status_code == 204
    assert client.get("/funcionarios?incluir_inativos=true", headers=auth_header(sindico)).json() == []


def test_zelador_cadastra_prestador_com_custo(client, db_session):
    _, _, _, _, zelador = _cenario(db_session)
    resposta = client.post(
        "/prestadores-servico",
        json={
            "nome": "Limpa Bem",
            "tipo_servico": "Limpeza",
            "razao_social": "Limpa Bem Serviços Ltda",
            "cnpj": "12.345.678/0001-99",
            "custo_mensal": "1000.00",
            "incluir_no_rateio": True,
        },
        headers=auth_header(zelador),
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["cnpj"] == "12345678000199"
    assert corpo["custo_mensal"] == "1000.00"
    assert corpo["incluir_no_rateio"] is True
    assert corpo["criterio_rateio"] == "igual"


def test_lancar_custo_com_rateio_divide_entre_unidades(client, db_session):
    _, _, _, sindico, _ = _cenario(db_session)
    p = client.post(
        "/prestadores-servico",
        json={"nome": "Limpa Bem", "tipo_servico": "Limpeza", "custo_mensal": "1000.00", "incluir_no_rateio": True},
        headers=auth_header(sindico),
    ).json()

    resposta = client.post(
        f"/prestadores-servico/{p['id']}/lancar-custo",
        json={"data_vencimento": str(date(2026, 10, 10))},
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 201
    despesa = resposta.json()
    assert despesa["valor"] == "1000.00"
    assert despesa["categoria"] == "Limpeza"
    assert despesa["rateado_em"] is not None
    assert sorted(i["valor"] for i in despesa["itens_rateio"]) == ["500.00", "500.00"]

    historico = client.get(f"/prestadores-servico/{p['id']}/lancamentos", headers=auth_header(sindico)).json()
    assert [d["id"] for d in historico] == [despesa["id"]]


def test_lancar_custo_sem_rateio_nao_cobra_unidades(client, db_session):
    _, _, _, sindico, _ = _cenario(db_session)
    p = client.post(
        "/prestadores-servico",
        json={"nome": "Jardim Verde", "tipo_servico": "Jardinagem", "custo_mensal": "400.00"},
        headers=auth_header(sindico),
    ).json()

    despesa = client.post(
        f"/prestadores-servico/{p['id']}/lancar-custo",
        json={"data_vencimento": str(date(2026, 10, 5))},
        headers=auth_header(sindico),
    ).json()
    assert despesa["rateado_em"] is None
    assert despesa["itens_rateio"] == []


def test_lancar_custo_duas_vezes_no_mesmo_mes_retorna_409(client, db_session):
    _, _, _, sindico, _ = _cenario(db_session)
    p = client.post(
        "/prestadores-servico",
        json={"nome": "Elevadores SA", "tipo_servico": "Elevadores", "custo_mensal": "900.00"},
        headers=auth_header(sindico),
    ).json()
    url = f"/prestadores-servico/{p['id']}/lancar-custo"

    assert client.post(url, json={"data_vencimento": "2026-11-05"}, headers=auth_header(sindico)).status_code == 201
    assert client.post(url, json={"data_vencimento": "2026-11-20"}, headers=auth_header(sindico)).status_code == 409
    assert client.post(url, json={"data_vencimento": "2026-12-05"}, headers=auth_header(sindico)).status_code == 201


def test_zelador_nao_lanca_custo(client, db_session):
    _, _, _, sindico, zelador = _cenario(db_session)
    p = client.post(
        "/prestadores-servico",
        json={"nome": "Dedetiza", "tipo_servico": "Dedetização", "custo_mensal": "300.00"},
        headers=auth_header(zelador),
    ).json()

    resposta = client.post(
        f"/prestadores-servico/{p['id']}/lancar-custo",
        json={"data_vencimento": "2026-10-10"},
        headers=auth_header(zelador),
    )
    assert resposta.status_code == 403
