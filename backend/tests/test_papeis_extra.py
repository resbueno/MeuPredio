from __future__ import annotations

from app.models.enums import RoleEnum
from app.models.usuario import Usuario
from tests.utils import auth_header, make_predio, make_unidade, make_user


def test_sindico_cria_usuario_com_papel_extra_morador(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.pe1@test.local", role=RoleEnum.SINDICO, predio=predio)

    resposta = client.post(
        "/usuarios",
        json={
            "email": "morador.pe1@test.dev",
            "full_name": "Fulano",
            "role": "sindico",
            "papeis_extra": ["morador"],
            "unidade_ids": [unidade.id],
            "password": "SenhaForte123!",
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 201
    assert resposta.json()["papeis_extra"] == ["morador"]


def test_administrador_nao_pode_ter_papel_extra(client, db_session):
    admin = make_user(db_session, email="admin.pe1@test.local", role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)

    resposta = client.post(
        "/usuarios",
        json={
            "email": "x.pe1@test.dev",
            "full_name": "Fulano",
            "role": "administrador",
            "papeis_extra": ["sindico"],
            "password": "SenhaForte123!",
        },
        headers=auth_header(admin),
    )
    assert resposta.status_code == 422


def test_administrador_nao_pode_ser_papel_extra(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.pe2@test.local", role=RoleEnum.SINDICO, predio=predio)

    resposta = client.post(
        "/usuarios",
        json={
            "email": "y.pe2@test.dev",
            "full_name": "Fulano",
            "role": "morador",
            "papeis_extra": ["administrador"],
            "unidade_ids": [unidade.id],
            "password": "SenhaForte123!",
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 422


def test_papel_extra_nao_pode_repetir_papel_principal(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.pe3@test.local", role=RoleEnum.SINDICO, predio=predio)

    resposta = client.post(
        "/usuarios",
        json={
            "email": "z.pe3@test.dev",
            "full_name": "Fulano",
            "role": "morador",
            "papeis_extra": ["morador"],
            "unidade_ids": [unidade.id],
            "password": "SenhaForte123!",
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 422


def test_patch_substitui_lista_de_papeis_extra(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.pe4@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session, email="morador.pe4@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )

    primeiro = client.patch(
        f"/usuarios/{morador.id}",
        json={"papeis_extra": ["proprietario"]},
        headers=auth_header(sindico),
    )
    assert primeiro.status_code == 200
    assert primeiro.json()["papeis_extra"] == ["proprietario"]

    segundo = client.patch(
        f"/usuarios/{morador.id}",
        json={"papeis_extra": []},
        headers=auth_header(sindico),
    )
    assert segundo.status_code == 200
    assert segundo.json()["papeis_extra"] == []


def test_morador_com_papel_extra_sindico_acessa_endpoint_de_sindico(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    morador_sindico = make_user(
        db_session,
        email="morador.pe5@test.local",
        role=RoleEnum.MORADOR,
        predio=predio,
        unidades=[unidade],
        papeis_extra=[RoleEnum.SINDICO],
    )

    # POST /despesas exige _FINANCEIRO = (ADMINISTRADOR, SINDICO) - um
    # morador puro levaria 403; com o papel extra de sindico, passa.
    resposta = client.post(
        "/despesas",
        json={
            "descricao": "Conta de teste",
            "categoria": "outros",
            "valor": "10",
            "data_vencimento": "2026-12-01",
        },
        headers=auth_header(morador_sindico),
    )
    assert resposta.status_code == 201


def test_morador_puro_nao_acessa_endpoint_de_sindico(client, db_session):
    morador = make_user(db_session, email="morador.pe6@test.local", role=RoleEnum.MORADOR)
    resposta = client.post(
        "/despesas",
        json={
            "descricao": "Conta de teste",
            "categoria": "outros",
            "valor": "10",
            "data_vencimento": "2026-12-01",
        },
        headers=auth_header(morador),
    )
    assert resposta.status_code == 403


def test_aviso_direto_visivel_por_papel_extra_proprietario(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.pe7@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador_proprietario = make_user(
        db_session,
        email="morador.pe7@test.local",
        role=RoleEnum.MORADOR,
        predio=predio,
        unidades=[unidade],
        papeis_extra=[RoleEnum.PROPRIETARIO],
    )

    criado = client.post(
        "/avisos-diretos",
        json={
            "unidade_id": unidade.id,
            "destinatario": "proprietario",
            "tipo": "aviso",
            "titulo": "IPTU",
            "mensagem": "Documento disponivel na portaria.",
        },
        headers=auth_header(sindico),
    ).json()

    # So visivel pelo papel PROPRIETARIO - o papel principal desta pessoa e
    # morador, mas o papel extra basta.
    resposta = client.get(f"/avisos-diretos/{criado['id']}", headers=auth_header(morador_proprietario))
    assert resposta.status_code == 200

    na_listagem = client.get("/avisos-diretos", headers=auth_header(morador_proprietario)).json()
    assert any(a["id"] == criado["id"] for a in na_listagem)
