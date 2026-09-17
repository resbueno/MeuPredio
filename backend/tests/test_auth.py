from __future__ import annotations

from app.models.enums import RoleEnum
from tests.utils import login_form, make_predio, make_user


def test_login_com_credenciais_validas(client, db_session):
    user = make_user(db_session, email="login1@test.local", role=RoleEnum.MORADOR, password="SenhaForte123!")
    response = client.post("/auth/login", data=login_form("login1@test.local", "SenhaForte123!", user.predio_id))
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_com_senha_errada(client, db_session):
    user = make_user(db_session, email="login2@test.local", role=RoleEnum.MORADOR, password="SenhaForte123!")
    response = client.post("/auth/login", data=login_form("login2@test.local", "senha-errada", user.predio_id))
    assert response.status_code == 401


def test_login_usuario_inexistente(client, db_session):
    predio = make_predio(db_session)
    response = client.post("/auth/login", data=login_form("naoexiste@test.local", "qualquercoisa", predio.id))
    assert response.status_code == 401


def test_login_usuario_inativo_retorna_403(client, db_session):
    user = make_user(
        db_session,
        email="inativo@test.local",
        role=RoleEnum.MORADOR,
        password="SenhaForte123!",
        is_active=False,
    )
    response = client.post("/auth/login", data=login_form("inativo@test.local", "SenhaForte123!", user.predio_id))
    assert response.status_code == 403


def test_login_sem_predio_id_so_autentica_administrador(client, db_session):
    """Omitir predio_id no login é o atalho reservado ao administrador
    (global, sem prédio) - um morador com o mesmo e-mail nunca é encontrado
    por essa consulta, mesmo que exista em algum prédio."""
    make_user(db_session, email="morador.sem.predio@test.local", role=RoleEnum.MORADOR)
    response = client.post(
        "/auth/login", data=login_form("morador.sem.predio@test.local", "SenhaForte123!", None)
    )
    assert response.status_code == 401


def test_login_com_predio_id_de_outro_predio_falha(client, db_session):
    """Isolamento multi-tenant no próprio login: um usuário só autentica
    informando o predio_id do SEU prédio - o de outro prédio (mesmo que
    válido) não encontra ninguém com este e-mail."""
    predio_a = make_predio(db_session)
    predio_b = make_predio(db_session)
    make_user(db_session, email="morador.a@test.local", role=RoleEnum.MORADOR, predio=predio_a)

    response = client.post(
        "/auth/login", data=login_form("morador.a@test.local", "SenhaForte123!", predio_b.id)
    )
    assert response.status_code == 401


def test_acesso_sem_token_retorna_401(client):
    response = client.get("/usuarios")
    assert response.status_code == 401


def test_token_invalido_retorna_401(client):
    response = client.get("/usuarios", headers={"Authorization": "Bearer token-forjado-invalido"})
    assert response.status_code == 401
