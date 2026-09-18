from __future__ import annotations

from app.models.enums import RoleEnum
from tests.utils import auth_header, make_predio, make_unidade, make_user


def test_sindico_envia_aviso_direto_e_morador_ve(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.ad1@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session, email="morador.ad1@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )

    criado = client.post(
        "/avisos-diretos",
        json={
            "unidade_id": unidade.id,
            "destinatario": "morador",
            "tipo": "aviso",
            "titulo": "Barulho",
            "mensagem": "Reclamacao de vizinho registrada.",
        },
        headers=auth_header(sindico),
    )
    assert criado.status_code == 201
    aviso_id = criado.json()["id"]

    visto = client.get(f"/avisos-diretos/{aviso_id}", headers=auth_header(morador))
    assert visto.status_code == 200


def test_morador_nao_ve_aviso_de_outra_unidade(client, db_session):
    predio = make_predio(db_session)
    unidade_alvo = make_unidade(db_session, predio, bloco="A", numero="1")
    unidade_outra = make_unidade(db_session, predio, bloco="B", numero="2")
    sindico = make_user(db_session, email="sindico.ad2@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador_alheio = make_user(
        db_session,
        email="morador.ad2@test.local",
        role=RoleEnum.MORADOR,
        predio=predio,
        unidades=[unidade_outra],
    )

    criado = client.post(
        "/avisos-diretos",
        json={
            "unidade_id": unidade_alvo.id,
            "destinatario": "ambos",
            "tipo": "aviso",
            "titulo": "XX",
            "mensagem": "YY",
        },
        headers=auth_header(sindico),
    ).json()

    resposta = client.get(f"/avisos-diretos/{criado['id']}", headers=auth_header(morador_alheio))
    assert resposta.status_code == 404


def test_aviso_so_para_proprietario_nao_aparece_para_morador(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.ad3@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session, email="morador.ad3@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )
    proprietario = make_user(
        db_session,
        email="proprietario.ad3@test.local",
        role=RoleEnum.PROPRIETARIO,
        predio=predio,
        unidades=[unidade],
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

    assert client.get(f"/avisos-diretos/{criado['id']}", headers=auth_header(morador)).status_code == 404
    assert (
        client.get(f"/avisos-diretos/{criado['id']}", headers=auth_header(proprietario)).status_code
        == 200
    )


def test_morador_responde_uma_vez_e_segunda_resposta_falha(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.ad4@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session, email="morador.ad4@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )

    criado = client.post(
        "/avisos-diretos",
        json={"unidade_id": unidade.id, "destinatario": "ambos", "tipo": "aviso", "titulo": "XX", "mensagem": "YY"},
        headers=auth_header(sindico),
    ).json()

    primeira = client.post(
        f"/avisos-diretos/{criado['id']}/responder",
        json={"resposta": "Ok, entendido."},
        headers=auth_header(morador),
    )
    assert primeira.status_code == 200
    assert primeira.json()["resposta"] == "Ok, entendido."
    assert primeira.json()["lida_em"] is not None

    segunda = client.post(
        f"/avisos-diretos/{criado['id']}/responder",
        json={"resposta": "De novo"},
        headers=auth_header(morador),
    )
    assert segunda.status_code == 409


def test_marcar_como_lido(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.ad5@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session, email="morador.ad5@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )

    criado = client.post(
        "/avisos-diretos",
        json={"unidade_id": unidade.id, "destinatario": "ambos", "tipo": "aviso", "titulo": "XX", "mensagem": "YY"},
        headers=auth_header(sindico),
    ).json()

    lido = client.post(f"/avisos-diretos/{criado['id']}/marcar-lido", headers=auth_header(morador))
    assert lido.status_code == 200
    assert lido.json()["lida_em"] is not None


def test_multa_gera_despesa_exclusiva_da_unidade_e_conta_no_rateio(client, db_session):
    predio = make_predio(db_session)
    unidade_multada = make_unidade(db_session, predio, bloco="A", numero="1")
    unidade_normal = make_unidade(db_session, predio, bloco="B", numero="2")
    sindico = make_user(db_session, email="sindico.ad6@test.local", role=RoleEnum.SINDICO, predio=predio)
    morador = make_user(
        db_session,
        email="morador.ad6@test.local",
        role=RoleEnum.MORADOR,
        predio=predio,
        unidades=[unidade_multada],
    )
    outro_morador = make_user(
        db_session,
        email="morador.ad7@test.local",
        role=RoleEnum.MORADOR,
        predio=predio,
        unidades=[unidade_normal],
    )

    criado = client.post(
        "/avisos-diretos",
        json={
            "unidade_id": unidade_multada.id,
            "destinatario": "ambos",
            "tipo": "multa",
            "titulo": "Barulho apos 22h",
            "mensagem": "Reincidencia registrada.",
            "valor": "150.00",
            "data_vencimento": "2026-11-10",
        },
        headers=auth_header(sindico),
    )
    assert criado.status_code == 201
    corpo = criado.json()
    assert corpo["despesa_lancamento_id"] is not None

    despesa = client.get(f"/despesas/{corpo['despesa_lancamento_id']}", headers=auth_header(sindico)).json()
    assert despesa["unidade_id"] == unidade_multada.id
    assert despesa["valor"] == "150.00"
    assert despesa["status"] == "pendente"

    # Nao pode ratear uma despesa exclusiva de unidade entre todas.
    falha_rateio = client.post(
        f"/despesas/{corpo['despesa_lancamento_id']}/ratear",
        json={"criterio": "igual"},
        headers=auth_header(sindico),
    )
    assert falha_rateio.status_code == 409

    # So a unidade multada (e a gestao) enxerga essa despesa no Portal da
    # Transparencia - o morador de outra unidade nunca ve a multa alheia.
    visivel_para_multado = client.get(
        "/transparencia/despesas", params={"ano": 2026, "mes": 11}, headers=auth_header(morador)
    ).json()
    assert any(d["id"] == corpo["despesa_lancamento_id"] for d in visivel_para_multado)

    invisivel_para_outro = client.get(
        "/transparencia/despesas", params={"ano": 2026, "mes": 11}, headers=auth_header(outro_morador)
    ).json()
    assert all(d["id"] != corpo["despesa_lancamento_id"] for d in invisivel_para_outro)


def test_multa_exige_valor_e_vencimento(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    sindico = make_user(db_session, email="sindico.ad8@test.local", role=RoleEnum.SINDICO, predio=predio)

    resposta = client.post(
        "/avisos-diretos",
        json={
            "unidade_id": unidade.id,
            "destinatario": "ambos",
            "tipo": "multa",
            "titulo": "XX",
            "mensagem": "YY",
        },
        headers=auth_header(sindico),
    )
    assert resposta.status_code == 422


def test_zelador_nao_pode_emitir_aviso_direto(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    zelador = make_user(db_session, email="zelador.ad1@test.local", role=RoleEnum.ZELADOR, predio=predio)

    resposta = client.post(
        "/avisos-diretos",
        json={"unidade_id": unidade.id, "destinatario": "ambos", "tipo": "aviso", "titulo": "XX", "mensagem": "YY"},
        headers=auth_header(zelador),
    )
    assert resposta.status_code == 403
