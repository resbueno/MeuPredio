from __future__ import annotations

from app.models.enums import RoleEnum
from app.models.log_auditoria import LogAuditoria
from app.models.unidade import Unidade
from tests.utils import auth_header, make_predio, make_unidade, make_user


def test_criar_unidade_sem_autenticacao_retorna_401(client):
    response = client.post("/unidades", json={"bloco": "A", "numero": "101"})
    assert response.status_code == 401


def test_morador_nao_pode_criar_unidade(client, db_session):
    morador = make_user(db_session, email="morador.u1@test.local", role=RoleEnum.MORADOR)
    response = client.post(
        "/unidades", json={"bloco": "A", "numero": "101"}, headers=auth_header(morador)
    )
    assert response.status_code == 403


def test_sindico_cria_unidade_no_proprio_predio_e_gera_auditoria(client, db_session):
    sindico = make_user(db_session, email="sindico.u1@test.local", role=RoleEnum.SINDICO)
    response = client.post(
        "/unidades", json={"bloco": "A", "numero": "101"}, headers=auth_header(sindico)
    )
    assert response.status_code == 201
    body = response.json()
    assert body["bloco"] == "A"
    assert body["numero"] == "101"
    assert body["predio_id"] == sindico.predio_id

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


def test_cria_unidade_com_vaga_e_atualiza_vaga(client, db_session):
    sindico = make_user(db_session, email="sindico.u1b@test.local", role=RoleEnum.SINDICO)
    response = client.post(
        "/unidades",
        json={"bloco": "A", "numero": "102", "vaga": "12A"},
        headers=auth_header(sindico),
    )
    assert response.status_code == 201
    assert response.json()["vaga"] == "12A"

    unidade_id = response.json()["id"]
    atualizada = client.patch(
        f"/unidades/{unidade_id}", json={"vaga": "34"}, headers=auth_header(sindico)
    )
    assert atualizada.status_code == 200
    assert atualizada.json()["vaga"] == "34"


def test_sindico_nao_pode_escolher_outro_predio(client, db_session):
    """predio_id no payload é ignorado para quem já tem prédio próprio -
    isolamento nunca depende do cliente "se comportar"."""
    outro_predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.u1b@test.local", role=RoleEnum.SINDICO)
    response = client.post(
        "/unidades",
        json={"bloco": "X", "numero": "999", "predio_id": outro_predio.id},
        headers=auth_header(sindico),
    )
    assert response.status_code == 201
    assert response.json()["predio_id"] == sindico.predio_id


def test_administrador_precisa_informar_predio_id(client, db_session):
    admin = make_user(db_session, email="admin.u0@test.local", role=RoleEnum.ADMINISTRADOR)
    response = client.post("/unidades", json={"bloco": "B", "numero": "202"}, headers=auth_header(admin))
    assert response.status_code == 422


def test_criar_unidade_duplicada_bloco_numero_retorna_409(client, db_session):
    admin = make_user(db_session, email="admin.u1@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    client.post(
        "/unidades",
        json={"bloco": "B", "numero": "202", "predio_id": predio.id},
        headers=auth_header(admin),
    )
    response = client.post(
        "/unidades",
        json={"bloco": "B", "numero": "202", "predio_id": predio.id},
        headers=auth_header(admin),
    )
    assert response.status_code == 409


def test_mesmo_bloco_numero_permitido_em_predios_diferentes(client, db_session):
    admin = make_user(db_session, email="admin.u2@test.local", role=RoleEnum.ADMINISTRADOR)
    predio_a = make_predio(db_session)
    predio_b = make_predio(db_session)
    r1 = client.post(
        "/unidades",
        json={"bloco": "C", "numero": "303", "predio_id": predio_a.id},
        headers=auth_header(admin),
    )
    r2 = client.post(
        "/unidades",
        json={"bloco": "C", "numero": "303", "predio_id": predio_b.id},
        headers=auth_header(admin),
    )
    assert r1.status_code == 201
    assert r2.status_code == 201


def test_listar_unidades_qualquer_usuario_autenticado_restrito_ao_proprio_predio(client, db_session):
    predio = make_predio(db_session)
    morador = make_user(db_session, email="morador.u2@test.local", role=RoleEnum.MORADOR, predio=predio)
    admin = make_user(db_session, email="admin.u3@test.local", role=RoleEnum.ADMINISTRADOR)
    client.post(
        "/unidades",
        json={"bloco": "D", "numero": "404", "predio_id": predio.id},
        headers=auth_header(admin),
    )
    outro_predio = make_predio(db_session)
    client.post(
        "/unidades",
        json={"bloco": "Z", "numero": "999", "predio_id": outro_predio.id},
        headers=auth_header(admin),
    )

    response = client.get("/unidades", headers=auth_header(morador))
    assert response.status_code == 200
    ids_predio = {u["predio_id"] for u in response.json()}
    assert ids_predio == {predio.id}


def test_acesso_direto_a_unidade_de_outro_predio_retorna_404(client, db_session):
    predio_a = make_predio(db_session)
    predio_b = make_predio(db_session)
    sindico_a = make_user(db_session, email="sindico.u2@test.local", role=RoleEnum.SINDICO, predio=predio_a)
    admin = make_user(db_session, email="admin.u5@test.local", role=RoleEnum.ADMINISTRADOR)
    unidade_b = client.post(
        "/unidades",
        json={"bloco": "Y", "numero": "1", "predio_id": predio_b.id},
        headers=auth_header(admin),
    ).json()

    response = client.get(f"/unidades/{unidade_b['id']}", headers=auth_header(sindico_a))
    assert response.status_code == 404


def test_soft_delete_unidade(client, db_session):
    admin = make_user(db_session, email="admin.u4@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    criada = client.post(
        "/unidades",
        json={"bloco": "E", "numero": "505", "predio_id": predio.id},
        headers=auth_header(admin),
    ).json()

    response = client.delete(f"/unidades/{criada['id']}", headers=auth_header(admin))
    assert response.status_code == 204

    unidade = db_session.get(Unidade, criada["id"])
    db_session.refresh(unidade)
    assert unidade.deleted_at is not None

    listagem = client.get("/unidades", params={"predio_id": predio.id}, headers=auth_header(admin))
    ids = [u["id"] for u in listagem.json()]
    assert criada["id"] not in ids


def test_sindico_cria_lote_de_unidades(client, db_session):
    sindico = make_user(db_session, email="sindico.u2@test.local", role=RoleEnum.SINDICO)
    resposta = client.post(
        "/unidades/lote",
        json={
            "unidades": [
                {"bloco": "1", "numero": "01"},
                {"bloco": "1", "numero": "02"},
                {"bloco": "1", "numero": "03"},
                {"bloco": "1", "numero": "11"},
                {"bloco": "1", "numero": "12"},
                {"bloco": "1", "numero": "13"},
            ]
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert len(corpo) == 6
    assert all(u["predio_id"] == sindico.predio_id for u in corpo)
    assert {u["numero"] for u in corpo} == {"01", "02", "03", "11", "12", "13"}


def test_lote_com_numero_repetido_dentro_do_proprio_lote_retorna_422(client, db_session):
    sindico = make_user(db_session, email="sindico.u3@test.local", role=RoleEnum.SINDICO)
    resposta = client.post(
        "/unidades/lote",
        json={"unidades": [{"bloco": "1", "numero": "01"}, {"bloco": "1", "numero": "01"}]},
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 422


def test_lote_colidindo_com_unidade_existente_retorna_409(client, db_session):
    # So confere o status code, mesmo padrao das outras verificacoes de
    # conflito (ex.: test_criar_unidade_duplicada_bloco_numero_retorna_409):
    # apos um IntegrityError, o rollback() no router encerra a savepoint
    # desta sessao de teste (limitacao do harness, inofensiva em producao -
    # la cada requisicao tem sua propria transacao) - consultar o banco
    # de novo na mesma sessao depois disso nao e confiavel aqui.
    sindico = make_user(db_session, email="sindico.u4@test.local", role=RoleEnum.SINDICO)
    make_unidade(db_session, sindico.predio, bloco="1", numero="02")

    resposta = client.post(
        "/unidades/lote",
        json={
            "unidades": [
                {"bloco": "1", "numero": "01"},
                {"bloco": "1", "numero": "02"},
            ]
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 409


def test_administrador_lote_precisa_informar_predio_id(client, db_session):
    admin = make_user(db_session, email="admin.u5@test.local", role=RoleEnum.ADMINISTRADOR)
    resposta = client.post(
        "/unidades/lote",
        json={"unidades": [{"bloco": "1", "numero": "01"}]},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 422
