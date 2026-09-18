from __future__ import annotations

import pytest
from sqlalchemy.exc import DBAPIError

from app.models.enums import RoleEnum
from app.models.log_auditoria import LogAuditoria
from app.models.usuario import Usuario
from tests.utils import auth_header, make_predio, make_unidade, make_user


def test_criar_usuario_sem_autenticacao_retorna_401(client):
    response = client.post(
        "/usuarios",
        json={"email": "x@test.local", "full_name": "X", "role": "morador", "password": "Senha1234"},
    )
    assert response.status_code == 401


def test_morador_nao_pode_criar_outros_usuarios(client, db_session):
    morador = make_user(db_session, email="morador1@test.local", role=RoleEnum.MORADOR)
    response = client.post(
        "/usuarios",
        json={
            "email": "novo@test.local",
            "full_name": "Novo",
            "role": "morador",
            "password": "Senha1234",
        },
        headers=auth_header(morador),
    )
    assert response.status_code == 403


def test_administrador_cria_usuario_com_sucesso_e_gera_auditoria(client, db_session):
    admin = make_user(db_session, email="admin1@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    response = client.post(
        "/usuarios",
        json={
            "email": "morador.novo@test.dev",
            "full_name": "Morador Novo",
            "role": "morador",
            "password": "Senha1234",
            "predio_id": predio.id,
            "unidade_ids": [unidade.id],
        },
        headers=auth_header(admin),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "morador.novo@test.dev"
    assert "password" not in body
    assert "hashed_password" not in body

    criado = db_session.query(Usuario).filter(Usuario.email == "morador.novo@test.dev").one()
    log = (
        db_session.query(LogAuditoria)
        .filter(
            LogAuditoria.entidade == "usuarios",
            LogAuditoria.entidade_id == criado.id,
            LogAuditoria.acao == "CREATE",
        )
        .one_or_none()
    )
    assert log is not None
    assert log.usuario_id == admin.id
    assert "hashed_password" not in (log.dados_depois or {})


def test_sindico_nao_pode_criar_administrador(client, db_session):
    sindico = make_user(db_session, email="sindico1@test.local", role=RoleEnum.SINDICO)
    response = client.post(
        "/usuarios",
        json={
            "email": "outroadmin@test.dev",
            "full_name": "Outro Admin",
            "role": "administrador",
            "password": "Senha1234",
        },
        headers=auth_header(sindico),
    )
    assert response.status_code == 403


def test_listar_usuarios_zelador_nao_autorizado(client, db_session):
    zelador = make_user(db_session, email="zelador1@test.local", role=RoleEnum.ZELADOR)
    response = client.get("/usuarios", headers=auth_header(zelador))
    assert response.status_code == 403


def test_administrador_lista_usuarios(client, db_session):
    admin = make_user(db_session, email="admin2@test.local", role=RoleEnum.ADMINISTRADOR)
    make_user(db_session, email="morador9@test.local", role=RoleEnum.MORADOR)
    response = client.get("/usuarios", headers=auth_header(admin))
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_morador_pode_ver_proprio_cadastro(client, db_session):
    morador = make_user(db_session, email="morador2@test.local", role=RoleEnum.MORADOR)
    response = client.get(f"/usuarios/{morador.id}", headers=auth_header(morador))
    assert response.status_code == 200
    assert response.json()["id"] == morador.id


def test_morador_nao_pode_ver_cadastro_de_outro(client, db_session):
    morador1 = make_user(db_session, email="morador3@test.local", role=RoleEnum.MORADOR)
    morador2 = make_user(db_session, email="morador4@test.local", role=RoleEnum.MORADOR)
    response = client.get(f"/usuarios/{morador2.id}", headers=auth_header(morador1))
    assert response.status_code == 403


def test_morador_nao_pode_alterar_propria_role(client, db_session):
    morador = make_user(db_session, email="morador5@test.local", role=RoleEnum.MORADOR)
    response = client.patch(
        f"/usuarios/{morador.id}",
        json={"role": "administrador"},
        headers=auth_header(morador),
    )
    assert response.status_code == 403


def test_morador_pode_alterar_proprio_nome(client, db_session):
    morador = make_user(db_session, email="morador6@test.local", role=RoleEnum.MORADOR)
    response = client.patch(
        f"/usuarios/{morador.id}",
        json={"full_name": "Novo Nome"},
        headers=auth_header(morador),
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Novo Nome"


def test_soft_delete_usuario_gera_auditoria(client, db_session):
    admin = make_user(db_session, email="admin3@test.local", role=RoleEnum.ADMINISTRADOR)
    alvo = make_user(db_session, email="alvo@test.local", role=RoleEnum.MORADOR)

    response = client.delete(f"/usuarios/{alvo.id}", headers=auth_header(admin))
    assert response.status_code == 204

    db_session.refresh(alvo)
    assert alvo.deleted_at is not None
    assert alvo.is_active is False

    log = (
        db_session.query(LogAuditoria)
        .filter(
            LogAuditoria.entidade == "usuarios",
            LogAuditoria.entidade_id == alvo.id,
            LogAuditoria.acao == "SOFT_DELETE",
        )
        .one_or_none()
    )
    assert log is not None


def test_usuario_removido_nao_aparece_na_listagem_padrao(client, db_session):
    admin = make_user(db_session, email="admin4@test.local", role=RoleEnum.ADMINISTRADOR)
    alvo = make_user(db_session, email="alvo5@test.local", role=RoleEnum.MORADOR)
    client.delete(f"/usuarios/{alvo.id}", headers=auth_header(admin))

    response = client.get("/usuarios", headers=auth_header(admin))
    ids = [u["id"] for u in response.json()]
    assert alvo.id not in ids


def test_anonimizar_usuario_requer_administrador(client, db_session):
    sindico = make_user(db_session, email="sindico2@test.local", role=RoleEnum.SINDICO)
    alvo = make_user(db_session, email="alvo2@test.local", role=RoleEnum.MORADOR)
    response = client.post(f"/usuarios/{alvo.id}/anonimizar", headers=auth_header(sindico))
    assert response.status_code == 403


def test_anonimizar_usuario_com_sucesso(client, db_session):
    admin = make_user(db_session, email="admin5@test.local", role=RoleEnum.ADMINISTRADOR)
    alvo = make_user(
        db_session, email="alvo3@test.local", role=RoleEnum.MORADOR, full_name="Fulano de Tal"
    )

    response = client.post(f"/usuarios/{alvo.id}/anonimizar", headers=auth_header(admin))
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Usuario Anonimizado"
    assert body["email"] != "alvo3@test.local"

    db_session.refresh(alvo)
    assert alvo.anonymized_at is not None
    assert alvo.full_name == "Usuario Anonimizado"

    log = (
        db_session.query(LogAuditoria)
        .filter(
            LogAuditoria.entidade == "usuarios",
            LogAuditoria.entidade_id == alvo.id,
            LogAuditoria.acao == "ANONYMIZE",
        )
        .one_or_none()
    )
    assert log is not None
    assert log.dados_depois["email"] != "alvo3@test.local"


def test_anonimizar_usuario_ja_anonimizado_retorna_409(client, db_session):
    admin = make_user(db_session, email="admin6@test.local", role=RoleEnum.ADMINISTRADOR)
    alvo = make_user(db_session, email="alvo6@test.local", role=RoleEnum.MORADOR)
    client.post(f"/usuarios/{alvo.id}/anonimizar", headers=auth_header(admin))

    response = client.post(f"/usuarios/{alvo.id}/anonimizar", headers=auth_header(admin))
    assert response.status_code == 409


def test_criar_usuario_sem_unidade_retorna_422(client, db_session):
    sindico = make_user(db_session, email="sindico3@test.local", role=RoleEnum.SINDICO)
    response = client.post(
        "/usuarios",
        json={
            "email": "semunidade@test.dev",
            "full_name": "Sem Unidade",
            "role": "morador",
            "password": "Senha1234",
        },
        headers=auth_header(sindico),
    )
    assert response.status_code == 422


def test_sindico_cria_usuario_ignora_predio_id_do_payload(client, db_session):
    """predio_id no payload é ignorado para quem já tem prédio próprio -
    a unidade tem que existir DENTRO do prédio do síndico, não do prédio
    que ele tentou informar."""
    outro_predio = make_predio(db_session)
    outra_unidade = make_unidade(db_session, outro_predio)
    sindico = make_user(db_session, email="sindico4@test.local", role=RoleEnum.SINDICO)

    response = client.post(
        "/usuarios",
        json={
            "email": "morador.x@test.dev",
            "full_name": "Morador X",
            "role": "morador",
            "password": "Senha1234",
            "predio_id": outro_predio.id,
            "unidade_ids": [outra_unidade.id],
        },
        headers=auth_header(sindico),
    )
    # A unidade informada não pertence ao prédio do síndico (que é o que
    # de fato vale) - 404, isolamento nunca depende do payload do cliente.
    assert response.status_code == 404


def test_sindico_nao_ve_usuario_de_outro_predio(client, db_session):
    predio_a = make_predio(db_session)
    predio_b = make_predio(db_session)
    sindico_a = make_user(db_session, email="sindico5@test.local", role=RoleEnum.SINDICO, predio=predio_a)
    morador_b = make_user(db_session, email="morador.b1@test.local", role=RoleEnum.MORADOR, predio=predio_b)

    resposta_get = client.get(f"/usuarios/{morador_b.id}", headers=auth_header(sindico_a))
    assert resposta_get.status_code == 404

    resposta_lista = client.get("/usuarios", headers=auth_header(sindico_a))
    ids = [u["id"] for u in resposta_lista.json()]
    assert morador_b.id not in ids


def test_proprietario_pode_ter_mais_de_uma_unidade(client, db_session):
    predio = make_predio(db_session)
    unidade1 = make_unidade(db_session, predio, bloco="A", numero="10")
    unidade2 = make_unidade(db_session, predio, bloco="A", numero="20")
    admin = make_user(db_session, email="admin7@test.local", role=RoleEnum.ADMINISTRADOR)

    response = client.post(
        "/usuarios",
        json={
            "email": "dono@test.dev",
            "full_name": "Dono de Duas Unidades",
            "role": "proprietario",
            "password": "Senha1234",
            "predio_id": predio.id,
            "unidade_ids": [unidade1.id, unidade2.id],
        },
        headers=auth_header(admin),
    )
    assert response.status_code == 201
    assert sorted(response.json()["unidade_ids"]) == sorted([unidade1.id, unidade2.id])


def test_log_auditoria_e_imutavel_via_trigger_de_banco(db_session):
    """O trigger de banco (migration 0002) deve bloquear UPDATE/DELETE mesmo
    quando o código tenta alterar a linha diretamente via ORM, contornando
    a aplicação por completo."""
    log = LogAuditoria(acao="TESTE", entidade="usuarios", entidade_id=1)
    db_session.add(log)
    db_session.flush()

    log.acao = "ALTERADO"
    with pytest.raises(DBAPIError):
        db_session.flush()


def test_usuario_aceita_o_proprio_consentimento_lgpd(client, db_session):
    morador = make_user(db_session, email="morador.lgpd1@test.local", role=RoleEnum.MORADOR)
    assert morador.consent_lgpd_accepted_at is None

    resposta = client.post(
        f"/usuarios/{morador.id}/consentimento-lgpd/aceitar", headers=auth_header(morador)
    )
    assert resposta.status_code == 200
    assert resposta.json()["consent_lgpd_accepted_at"] is not None

    revogada = client.post(
        f"/usuarios/{morador.id}/consentimento-lgpd/revogar", headers=auth_header(morador)
    )
    assert revogada.status_code == 200
    assert revogada.json()["consent_lgpd_accepted_at"] is None


def test_sindico_nao_pode_aceitar_consentimento_de_outro(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.lgpd1@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session, email="morador.lgpd2@test.local", role=RoleEnum.MORADOR, predio=predio
    )

    resposta = client.post(
        f"/usuarios/{morador.id}/consentimento-lgpd/aceitar", headers=auth_header(sindico)
    )
    assert resposta.status_code == 403
