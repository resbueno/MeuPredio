from __future__ import annotations

from app.models.enums import RoleEnum
from app.models.log_auditoria import LogAuditoria
from app.models.unidade import Unidade
from tests.utils import auth_header, make_user


def test_criar_unidade_sem_autenticacao_retorna_401(client):
    response = client.post("/unidades", json={"bloco": "A", "numero": "101"})
    assert response.status_code == 401


def test_morador_nao_pode_criar_unidade(client, db_session):
    morador = make_user(db_session, email="morador.u1@test.local", role=RoleEnum.MORADOR)
    response = client.post(
        "/unidades", json={"bloco": "A", "numero": "101"}, headers=auth_header(morador)
    )
    assert response.status_code == 403


def test_sindico_cria_unidade_com_sucesso_e_gera_auditoria(client, db_session):
    sindico = make_user(db_session, email="sindico.u1@test.local", role=RoleEnum.SINDICO)
    response = client.post(
        "/unidades", json={"bloco": "A", "numero": "101"}, headers=auth_header(sindico)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["bloco"] == "A"
    assert body["numero"] == "101"

    criada = db_session.query(Unidade).filter(Unidade.id == body["id"]).one()
    log = (
        db_session.query(LogAuditoria)
        .filter(
            LogAuditoria.entidade == "unidades",
            LogAuditoria.entidade_id == criada.id,
            LogAuditoria.acao == "CREATE",
        )
        .one_or_none()
    )
    assert log is not None


def test_criar_unidade_duplicada_bloco_numero_retorna_409(client, db_session):
    admin = make_user(db_session, email="admin.u1@test.local", role=RoleEnum.ADMINISTRADOR)
    client.post("/unidades", json={"bloco": "B", "numero": "202"}, headers=auth_header(admin))
    response = client.post(
        "/unidades", json={"bloco": "B", "numero": "202"}, headers=auth_header(admin)
    )
    assert response.status_code == 409


def test_criar_unidade_com_proprietario_inexistente_retorna_404(client, db_session):
    admin = make_user(db_session, email="admin.u2@test.local", role=RoleEnum.ADMINISTRADOR)
    response = client.post(
        "/unidades",
        json={"bloco": "C", "numero": "303", "proprietario_id": 999999},
        headers=auth_header(admin),
    )
    assert response.status_code == 404


def test_listar_unidades_qualquer_usuario_autenticado(client, db_session):
    morador = make_user(db_session, email="morador.u2@test.local", role=RoleEnum.MORADOR)
    admin = make_user(db_session, email="admin.u3@test.local", role=RoleEnum.ADMINISTRADOR)
    client.post("/unidades", json={"bloco": "D", "numero": "404"}, headers=auth_header(admin))

    response = client.get("/unidades", headers=auth_header(morador))
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_soft_delete_unidade(client, db_session):
    admin = make_user(db_session, email="admin.u4@test.local", role=RoleEnum.ADMINISTRADOR)
    criada = client.post(
        "/unidades", json={"bloco": "E", "numero": "505"}, headers=auth_header(admin)
    ).json()

    response = client.delete(f"/unidades/{criada['id']}", headers=auth_header(admin))
    assert response.status_code == 204

    unidade = db_session.get(Unidade, criada["id"])
    db_session.refresh(unidade)
    assert unidade.deleted_at is not None

    listagem = client.get("/unidades", headers=auth_header(admin))
    ids = [u["id"] for u in listagem.json()]
    assert criada["id"] not in ids
