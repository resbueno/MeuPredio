from __future__ import annotations

from app.models.enums import RoleEnum
from tests.utils import make_user


def test_login_com_credenciais_validas(client, db_session):
    make_user(db_session, email="login1@test.local", role=RoleEnum.MORADOR, password="SenhaForte123!")
    response = client.post(
        "/auth/login",
        data={"username": "login1@test.local", "password": "SenhaForte123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_com_senha_errada(client, db_session):
    make_user(db_session, email="login2@test.local", role=RoleEnum.MORADOR, password="SenhaForte123!")
    response = client.post(
        "/auth/login",
        data={"username": "login2@test.local", "password": "senha-errada"},
    )
    assert response.status_code == 401


def test_login_usuario_inexistente(client):
    response = client.post(
        "/auth/login",
        data={"username": "naoexiste@test.local", "password": "qualquercoisa"},
    )
    assert response.status_code == 401


def test_login_usuario_inativo_retorna_403(client, db_session):
    make_user(
        db_session,
        email="inativo@test.local",
        role=RoleEnum.MORADOR,
        password="SenhaForte123!",
        is_active=False,
    )
    response = client.post(
        "/auth/login",
        data={"username": "inativo@test.local", "password": "SenhaForte123!"},
    )
    assert response.status_code == 403


def test_acesso_sem_token_retorna_401(client):
    response = client.get("/usuarios")
    assert response.status_code == 401


def test_token_invalido_retorna_401(client):
    response = client.get("/usuarios", headers={"Authorization": "Bearer token-forjado-invalido"})
    assert response.status_code == 401
