from __future__ import annotations

import pytest

from app.core.viacep import CepNaoEncontradoError, EnderecoViaCep
from app.models.enums import RoleEnum
from tests.utils import auth_header, login_form, make_predio, make_unidade, make_user


@pytest.fixture(autouse=True)
def _mock_viacep(monkeypatch):
    """Nenhum teste desta suíte deve depender de rede real - o ViaCEP é
    sempre mockado, com um endereço fixo e previsível."""

    def _fake_consultar_cep(cep: str, *, timeout: float = 5.0) -> EnderecoViaCep:
        if cep.replace("-", "") == "00000000":
            raise CepNaoEncontradoError("CEP nao encontrado (mock).")
        return EnderecoViaCep(logradouro="Rua Teste", bairro="Centro", cidade="Sao Paulo", uf="SP")

    monkeypatch.setattr("app.routers.predios.consultar_cep", _fake_consultar_cep)


def test_criar_predio_sem_autenticacao_retorna_401(client):
    response = client.post("/predios", json={"nome": "Edificio X", "cep": "01310-100", "numero": "100"})
    assert response.status_code == 401


def test_sindico_nao_pode_criar_predio(client, db_session):
    sindico = make_user(db_session, email="sindico.p1@test.local", role=RoleEnum.SINDICO)
    response = client.post(
        "/predios",
        json={"nome": "Edificio X", "cep": "01310-100", "numero": "100"},
        headers=auth_header(sindico),
    )
    assert response.status_code == 403


def test_admin_cria_predio_com_unidades_e_endereco_via_cep(client, db_session):
    admin = make_user(db_session, email="admin.p1@test.local", role=RoleEnum.ADMINISTRADOR)
    response = client.post(
        "/predios",
        json={
            "nome": "Edificio Aurora",
            "cep": "01310-100",
            "numero": "1000",
            "unidades": [{"bloco": "A", "numero": "101"}, {"bloco": "A", "numero": "102"}],
        },
        headers=auth_header(admin),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["logradouro"] == "Rua Teste"
    assert body["cidade"] == "Sao Paulo"
    assert body["uf"] == "SP"

    unidades = client.get("/unidades", params={"predio_id": body["id"]}, headers=auth_header(admin)).json()
    assert len(unidades) == 2


def test_cep_nao_encontrado_retorna_404(client, db_session):
    admin = make_user(db_session, email="admin.p2@test.local", role=RoleEnum.ADMINISTRADOR)
    response = client.post(
        "/predios",
        json={"nome": "Edificio Y", "cep": "00000-000", "numero": "1"},
        headers=auth_header(admin),
    )
    assert response.status_code == 404


def test_predio_duplicado_cep_numero_retorna_409(client, db_session):
    admin = make_user(db_session, email="admin.p3@test.local", role=RoleEnum.ADMINISTRADOR)
    payload = {"nome": "Edificio Z", "cep": "01310-100", "numero": "500"}
    client.post("/predios", json=payload, headers=auth_header(admin))
    response = client.post("/predios", json=payload, headers=auth_header(admin))
    assert response.status_code == 409


def test_identificar_predio_publico(client, db_session):
    predio = make_predio(db_session, nome="Edificio Encontravel")
    response = client.post("/predios/identificar", json={"cep": predio.cep, "numero": predio.numero})
    assert response.status_code == 200
    assert response.json()["id"] == predio.id
    assert response.json()["nome"] == "Edificio Encontravel"


def test_identificar_predio_inexistente_retorna_404(client):
    response = client.post("/predios/identificar", json={"cep": "12345678", "numero": "999999"})
    assert response.status_code == 404


def test_gerar_convite_e_fluxo_de_autocadastro(client, db_session):
    admin = make_user(db_session, email="admin.p4@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio, bloco="B", numero="1")

    convite = client.post(f"/predios/{predio.id}/convite", headers=auth_header(admin)).json()
    assert convite["ativo"] is True
    token = convite["token"]

    info = client.get(f"/predios/convite/{token}").json()
    assert info["predio_id"] == predio.id
    assert any(u["id"] == unidade.id for u in info["unidades"])

    cadastro = client.post(
        f"/predios/convite/{token}/cadastro",
        json={
            "email": "novomorador@test.dev",
            "password": "SenhaForte123!",
            "full_name": "Novo Morador",
            "role": "morador",
            "unidade_ids": [unidade.id],
        },
    )
    assert cadastro.status_code == 201


def test_admin_edita_nome_do_predio(client, db_session):
    admin = make_user(db_session, email="admin.pe1@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session, nome="Nome Antigo")

    response = client.patch(
        f"/predios/{predio.id}", json={"nome": "Nome Novo"}, headers=auth_header(admin)
    )
    assert response.status_code == 200
    assert response.json()["nome"] == "Nome Novo"
    assert response.json()["cep"] == predio.cep


def test_editar_cep_refaz_consulta_viacep(client, db_session):
    admin = make_user(db_session, email="admin.pe2@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session, cep="10000001", numero="1")

    response = client.patch(
        f"/predios/{predio.id}",
        json={"cep": "01310-100"},
        headers=auth_header(admin),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cep"] == "01310100"
    assert body["logradouro"] == "Rua Teste"


def test_editar_para_cep_numero_ja_usado_retorna_409(client, db_session):
    admin = make_user(db_session, email="admin.pe3@test.local", role=RoleEnum.ADMINISTRADOR)
    predio_a = make_predio(db_session, cep="10000002", numero="2")
    predio_b = make_predio(db_session, cep="10000003", numero="3")

    response = client.patch(
        f"/predios/{predio_b.id}",
        json={"cep": predio_a.cep, "numero": predio_a.numero},
        headers=auth_header(admin),
    )
    assert response.status_code == 409


def test_sindico_nao_pode_editar_predio(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.pe1@test.local", role=RoleEnum.SINDICO, predio=predio)
    response = client.patch(
        f"/predios/{predio.id}", json={"nome": "Tentativa"}, headers=auth_header(sindico)
    )
    assert response.status_code == 403


def test_novo_predio_nasce_com_todos_os_modulos_habilitados(client, db_session):
    admin = make_user(db_session, email="admin.p5@test.local", role=RoleEnum.ADMINISTRADOR)
    response = client.post(
        "/predios",
        json={"nome": "Edificio Modular", "cep": "01310-100", "numero": "2000"},
        headers=auth_header(admin),
    )
    assert response.status_code == 201
    assert "financeiro" in response.json()["modulos_habilitados"]
    assert "visitantes" in response.json()["modulos_habilitados"]


def test_sindico_nao_pode_alterar_modulos(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.p5@test.local", role=RoleEnum.SINDICO, predio=predio)
    response = client.put(
        f"/predios/{predio.id}/modulos",
        json={"modulos_habilitados": ["financeiro"]},
        headers=auth_header(sindico),
    )
    assert response.status_code == 403


def test_admin_desabilita_modulo_e_bloqueia_acesso_do_predio(client, db_session):
    admin = make_user(db_session, email="admin.p6@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.p6@test.local", role=RoleEnum.SINDICO, predio=predio)

    resposta = client.put(
        f"/predios/{predio.id}/modulos",
        json={"modulos_habilitados": ["financeiro"]},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 200
    assert resposta.json()["modulos_habilitados"] == ["financeiro"]

    bloqueado = client.get("/visitantes", headers=auth_header(sindico))
    assert bloqueado.status_code == 403

    liberado = client.get("/despesas", headers=auth_header(sindico))
    assert liberado.status_code != 403
    novo_usuario = cadastro.json()
    assert novo_usuario["predio_id"] == predio.id
    assert novo_usuario["unidade_ids"] == [unidade.id]

    # E consegue logar de verdade com o que acabou de cadastrar.
    login = client.post(
        "/auth/login", data=login_form("novomorador@test.dev", "SenhaForte123!", predio.id)
    )
    assert login.status_code == 200


def test_autocadastro_nao_aceita_papel_de_equipe(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    admin = make_user(db_session, email="admin.p5@test.local", role=RoleEnum.ADMINISTRADOR)
    convite = client.post(f"/predios/{predio.id}/convite", headers=auth_header(admin)).json()

    response = client.post(
        f"/predios/convite/{convite['token']}/cadastro",
        json={
            "email": "fingesindico@test.dev",
            "password": "SenhaForte123!",
            "full_name": "Fake",
            "role": "sindico",
            "unidade_ids": [unidade.id],
        },
    )
    assert response.status_code == 422


def test_autocadastro_com_unidade_de_outro_predio_retorna_404(client, db_session):
    predio = make_predio(db_session)
    outro_predio = make_predio(db_session)
    unidade_alheia = make_unidade(db_session, outro_predio)
    admin = make_user(db_session, email="admin.p6@test.local", role=RoleEnum.ADMINISTRADOR)
    convite = client.post(f"/predios/{predio.id}/convite", headers=auth_header(admin)).json()

    response = client.post(
        f"/predios/convite/{convite['token']}/cadastro",
        json={
            "email": "morador@test.dev",
            "password": "SenhaForte123!",
            "full_name": "Morador",
            "role": "morador",
            "unidade_ids": [unidade_alheia.id],
        },
    )
    assert response.status_code == 404


def test_revogar_convite_invalida_cadastro_seguinte(client, db_session):
    admin = make_user(db_session, email="admin.p7@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    convite = client.post(f"/predios/{predio.id}/convite", headers=auth_header(admin)).json()

    revogar = client.delete(f"/predios/{predio.id}/convite", headers=auth_header(admin))
    assert revogar.status_code == 204

    info = client.get(f"/predios/convite/{convite['token']}")
    assert info.status_code == 404


def test_gerar_novo_convite_desativa_o_anterior(client, db_session):
    admin = make_user(db_session, email="admin.p8@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)

    convite1 = client.post(f"/predios/{predio.id}/convite", headers=auth_header(admin)).json()
    convite2 = client.post(f"/predios/{predio.id}/convite", headers=auth_header(admin)).json()

    assert convite1["token"] != convite2["token"]
    assert client.get(f"/predios/convite/{convite1['token']}").status_code == 404
    assert client.get(f"/predios/convite/{convite2['token']}").status_code == 200


def test_sindico_gera_convite_so_do_proprio_predio(client, db_session):
    outro_predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.p2@test.local", role=RoleEnum.SINDICO)

    response = client.post(f"/predios/{outro_predio.id}/convite", headers=auth_header(sindico))
    assert response.status_code == 403


def test_admin_lista_predios(client, db_session):
    admin = make_user(db_session, email="admin.p9@test.local", role=RoleEnum.ADMINISTRADOR)
    make_predio(db_session, nome="Predio Listavel")
    response = client.get("/predios", headers=auth_header(admin))
    assert response.status_code == 200
    assert any(p["nome"] == "Predio Listavel" for p in response.json())


def test_sindico_nao_pode_listar_predios(client, db_session):
    sindico = make_user(db_session, email="sindico.p3@test.local", role=RoleEnum.SINDICO)
    response = client.get("/predios", headers=auth_header(sindico))
    assert response.status_code == 403
