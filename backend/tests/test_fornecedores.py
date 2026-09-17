from __future__ import annotations

from app.models.enums import RoleEnum
from app.models.log_auditoria import LogAuditoria
from tests.utils import auth_header, make_user


def test_criar_fornecedor_sem_autenticacao_retorna_401(client):
    response = client.post(
        "/fornecedores",
        json={"nome": "Dedetizadora ABC", "categoria": "dedetizacao"},
    )
    assert response.status_code == 401


def test_morador_nao_pode_acessar_fornecedores(client, db_session):
    morador = make_user(db_session, email="morador.f1@test.local", role=RoleEnum.MORADOR)
    response = client.post(
        "/fornecedores",
        json={"nome": "Dedetizadora ABC", "categoria": "dedetizacao"},
        headers=auth_header(morador),
    )
    assert response.status_code == 403
    assert client.get("/fornecedores", headers=auth_header(morador)).status_code == 403


def test_zelador_nao_pode_acessar_fornecedores(client, db_session):
    zelador = make_user(db_session, email="zelador.f1@test.local", role=RoleEnum.ZELADOR)
    response = client.get("/fornecedores", headers=auth_header(zelador))
    assert response.status_code == 403


def test_sindico_cria_fornecedor_com_sucesso_e_normaliza_documento(client, db_session):
    sindico = make_user(db_session, email="sindico.f1@test.local", role=RoleEnum.SINDICO)
    response = client.post(
        "/fornecedores",
        json={
            "nome": "Jardinagem Verde Ltda",
            "documento": "12.345.678/0001-99",
            "categoria": "jardinagem",
            "telefone": "11999998888",
            "email": "contato@jardinagemverde.com.br",
        },
        headers=auth_header(sindico),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["documento"] == "12345678000199"

    log = (
        db_session.query(LogAuditoria)
        .filter(
            LogAuditoria.entidade == "fornecedores",
            LogAuditoria.entidade_id == body["id"],
            LogAuditoria.acao == "CREATE",
        )
        .one_or_none()
    )
    assert log is not None


def test_documento_invalido_e_rejeitado(client, db_session):
    sindico = make_user(db_session, email="sindico.f2@test.local", role=RoleEnum.SINDICO)
    response = client.post(
        "/fornecedores",
        json={"nome": "Fornecedor X", "documento": "123", "categoria": "manutencao"},
        headers=auth_header(sindico),
    )
    assert response.status_code == 422


def test_documento_duplicado_retorna_409(client, db_session):
    admin = make_user(db_session, email="admin.f1@test.local", role=RoleEnum.ADMINISTRADOR)
    payload = {"nome": "Fornecedor Y", "documento": "98765432000112", "categoria": "eletrica"}
    primeiro = client.post("/fornecedores", json=payload, headers=auth_header(admin))
    assert primeiro.status_code == 201

    segundo = client.post(
        "/fornecedores",
        json={**payload, "nome": "Fornecedor Y (duplicado)"},
        headers=auth_header(admin),
    )
    assert segundo.status_code == 409


def test_listar_filtra_por_categoria_e_ignora_soft_deleted(client, db_session):
    admin = make_user(db_session, email="admin.f2@test.local", role=RoleEnum.ADMINISTRADOR)
    f1 = client.post(
        "/fornecedores",
        json={"nome": "Limpeza A", "categoria": "limpeza"},
        headers=auth_header(admin),
    ).json()
    client.post(
        "/fornecedores",
        json={"nome": "Eletrica B", "categoria": "eletrica"},
        headers=auth_header(admin),
    )

    client.delete(f"/fornecedores/{f1['id']}", headers=auth_header(admin))

    resposta_categoria = client.get(
        "/fornecedores", params={"categoria": "eletrica"}, headers=auth_header(admin)
    )
    nomes = [f["nome"] for f in resposta_categoria.json()]
    assert nomes == ["Eletrica B"]

    resposta_geral = client.get("/fornecedores", headers=auth_header(admin))
    assert f1["id"] not in [f["id"] for f in resposta_geral.json()]
