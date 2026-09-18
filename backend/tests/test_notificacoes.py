from __future__ import annotations

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_unidade, make_user


def test_aviso_condominio_notifica_todos_menos_administrador_e_autor(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.no1@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(db_session, email="morador.no1@test.local", role=RoleEnum.MORADOR, predio=predio)

    resposta = client.post(
        "/avisos-mural",
        json={"tipo": "condominio", "titulo": "Manutenção do elevador", "descricao": "Amanhã, 9h."},
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 201

    notificacoes_morador = client.get("/notificacoes", headers=auth_header(morador)).json()
    assert len(notificacoes_morador) == 1
    assert notificacoes_morador[0]["tipo"] == "aviso_geral"

    # Autor nao notifica a si mesmo.
    assert client.get("/notificacoes", headers=auth_header(sindico)).json() == []


def test_aviso_mural_anuncio_nao_gera_notificacao(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.no2@test.local", role=RoleEnum.MORADOR, predio=predio)
    outro = make_user(db_session, email="morador.no3@test.local", role=RoleEnum.MORADOR, predio=predio)

    resposta = client.post(
        "/avisos-mural",
        json={"tipo": "anuncio", "titulo": "Vendo bicicleta", "descricao": "Semi-nova."},
        headers=auth_header(autor),
    )
    assert resposta.status_code == 201
    assert client.get("/notificacoes", headers=auth_header(outro)).json() == []


def test_aviso_direto_notifica_so_unidade_destino_com_papel_compativel(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.no2@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session, email="morador.no4@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )
    proprietario = make_user(
        db_session,
        email="proprietario.no1@test.local",
        role=RoleEnum.PROPRIETARIO,
        predio=predio,
        unidades=[unidade],
    )

    resposta = client.post(
        "/avisos-diretos",
        json={
            "unidade_id": unidade.id,
            "destinatario": "morador",
            "tipo": "aviso",
            "titulo": "Barulho",
            "mensagem": "Reduza o volume após 22h.",
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 201

    assert len(client.get("/notificacoes", headers=auth_header(morador)).json()) == 1
    # Destinatario == "morador": proprietario da mesma unidade nao recebe.
    assert client.get("/notificacoes", headers=auth_header(proprietario)).json() == []


def test_ocorrencia_notifica_sindico_mas_nao_zelador_nem_outro_morador(client, db_session):
    predio = make_predio(db_session)
    autor = make_user(db_session, email="morador.no5@test.local", role=RoleEnum.MORADOR, predio=predio)
    sindico = make_user(db_session, email="sindico.no3@test.local", role=RoleEnum.SINDICO, predio=predio)
    zelador = make_user(db_session, email="zelador.no1@test.local", role=RoleEnum.ZELADOR, predio=predio)

    resposta = client.post(
        "/ocorrencias",
        json={"titulo": "Vazamento", "descricao": "Garagem, vaga 5."},
        headers=auth_header(autor),
    )
    assert resposta.status_code == 201

    assert len(client.get("/notificacoes", headers=auth_header(sindico)).json()) == 1
    assert client.get("/notificacoes", headers=auth_header(zelador)).json() == []


def test_reuniao_convocada_notifica_predio_exceto_convocador(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.no4@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(db_session, email="morador.no6@test.local", role=RoleEnum.MORADOR, predio=predio)

    resposta = client.post(
        "/reunioes",
        json={
            "tipo": "ordinaria",
            "titulo": "Assembleia anual",
            "data_hora": "2026-12-01T19:00:00-03:00",
            "local": "Salão de festas",
            "pauta": "Prestação de contas.",
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 201

    assert len(client.get("/notificacoes", headers=auth_header(morador)).json()) == 1
    assert client.get("/notificacoes", headers=auth_header(sindico)).json() == []


def test_marcar_lida_e_marcar_todas_lidas(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.no5@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(db_session, email="morador.no7@test.local", role=RoleEnum.MORADOR, predio=predio)

    for titulo in ("Aviso 1", "Aviso 2"):
        client.post(
            "/avisos-mural",
            json={"tipo": "condominio", "titulo": titulo, "descricao": "..."},
            headers=auth_header(sindico),
        )

    contagem = client.get("/notificacoes/contagem-nao-lidas", headers=auth_header(morador)).json()
    assert contagem["nao_lidas"] == 2

    notificacoes = client.get("/notificacoes", headers=auth_header(morador)).json()
    primeira_id = notificacoes[0]["id"]

    lida = client.post(f"/notificacoes/{primeira_id}/marcar-lida", headers=auth_header(morador))
    assert lida.status_code == 200
    assert lida.json()["lida_em"] is not None

    contagem = client.get("/notificacoes/contagem-nao-lidas", headers=auth_header(morador)).json()
    assert contagem["nao_lidas"] == 1

    todas = client.post("/notificacoes/marcar-todas-lidas", headers=auth_header(morador))
    assert todas.status_code == 204

    contagem = client.get("/notificacoes/contagem-nao-lidas", headers=auth_header(morador)).json()
    assert contagem["nao_lidas"] == 0


def test_nao_pode_marcar_lida_notificacao_de_outro_usuario(client, db_session):
    predio = make_predio(db_session)
    sindico = make_user(db_session, email="sindico.no6@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(db_session, email="morador.no8@test.local", role=RoleEnum.MORADOR, predio=predio)
    outro = make_user(db_session, email="morador.no9@test.local", role=RoleEnum.MORADOR, predio=predio)

    client.post(
        "/avisos-mural",
        json={"tipo": "condominio", "titulo": "Aviso", "descricao": "..."},
        headers=auth_header(sindico),
    )
    notificacao_id = client.get("/notificacoes", headers=auth_header(morador)).json()[0]["id"]

    resposta = client.post(f"/notificacoes/{notificacao_id}/marcar-lida", headers=auth_header(outro))
    assert resposta.status_code == 404
