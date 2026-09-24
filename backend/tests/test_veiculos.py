from __future__ import annotations

from app.models.enums import RoleEnum
from app.models.log_auditoria import LogAuditoria
from app.models.veiculo import Veiculo
from tests.utils import auth_header, make_predio, make_unidade, make_user


def test_criar_veiculo_sem_autenticacao_retorna_401(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    response = client.post(
        "/veiculos",
        json={"unidade_id": unidade.id, "placa": "ABC1D23", "modelo": "Onix", "cor": "Prata"},
    )
    assert response.status_code == 401


def test_morador_nao_pode_criar_veiculo(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    morador = make_user(
        db_session, email="morador.v1@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade]
    )
    response = client.post(
        "/veiculos",
        json={"unidade_id": unidade.id, "placa": "ABC1D23", "modelo": "Onix", "cor": "Prata"},
        headers=auth_header(morador),
    )
    assert response.status_code == 403


def test_zelador_cria_veiculo_com_sucesso_e_normaliza_placa(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio)
    zelador = make_user(db_session, email="zelador.v1@test.local", role=RoleEnum.ZELADOR, predio=predio)
    response = client.post(
        "/veiculos",
        json={"unidade_id": unidade.id, "placa": " abc1d23 ", "modelo": "Onix", "cor": "Prata"},
        headers=auth_header(zelador),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["placa"] == "ABC1D23"

    log = (
        db_session.query(LogAuditoria)
        .filter(
            LogAuditoria.entidade == "veiculos",
            LogAuditoria.entidade_id == body["id"],
            LogAuditoria.acao == "CREATE",
        )
        .one_or_none()
    )
    assert log is not None


def test_criar_veiculo_unidade_inexistente_retorna_404(client, db_session):
    admin = make_user(db_session, email="admin.v1@test.local", role=RoleEnum.ADMINISTRADOR)
    response = client.post(
        "/veiculos",
        json={"unidade_id": 999999, "placa": "ABC1D23", "modelo": "Onix", "cor": "Prata"},
        headers=auth_header(admin),
    )
    assert response.status_code == 404


def test_sindico_nao_pode_criar_veiculo_em_unidade_de_outro_predio(client, db_session):
    predio_proprio = make_predio(db_session)
    predio_alheio = make_predio(db_session)
    unidade_alheia = make_unidade(db_session, predio_alheio)
    sindico = make_user(db_session, email="sindico.v1@test.local", role=RoleEnum.SINDICO, predio=predio_proprio)

    response = client.post(
        "/veiculos",
        json={"unidade_id": unidade_alheia.id, "placa": "ZZZ9999", "modelo": "Uno", "cor": "Azul"},
        headers=auth_header(sindico),
    )
    assert response.status_code == 404


def test_morador_ve_apenas_veiculos_das_proprias_unidades(client, db_session):
    predio = make_predio(db_session)
    unidade1 = make_unidade(db_session, predio, bloco="A", numero="1")
    unidade2 = make_unidade(db_session, predio, bloco="B", numero="2")
    admin = make_user(db_session, email="admin.v2@test.local", role=RoleEnum.ADMINISTRADOR)

    v1 = client.post(
        "/veiculos",
        json={"unidade_id": unidade1.id, "placa": "AAA1111", "modelo": "Gol", "cor": "Branco"},
        headers=auth_header(admin),
    ).json()
    client.post(
        "/veiculos",
        json={"unidade_id": unidade2.id, "placa": "BBB2222", "modelo": "Civic", "cor": "Preto"},
        headers=auth_header(admin),
    )

    morador = make_user(
        db_session, email="morador.v2@test.local", role=RoleEnum.MORADOR, predio=predio, unidades=[unidade1]
    )
    response = client.get("/veiculos", headers=auth_header(morador))
    assert response.status_code == 200
    placas = [v["placa"] for v in response.json()]
    assert placas == ["AAA1111"]

    # Não pode ver o veículo da outra unidade nem por acesso direto.
    outro_veiculo_id = (
        db_session.query(Veiculo).filter(Veiculo.unidade_id == unidade2.id).one().id
    )
    response_direto = client.get(f"/veiculos/{outro_veiculo_id}", headers=auth_header(morador))
    assert response_direto.status_code == 403
    assert v1["placa"] == "AAA1111"


def test_proprietario_com_duas_unidades_ve_veiculos_de_ambas(client, db_session):
    predio = make_predio(db_session)
    unidade1 = make_unidade(db_session, predio, bloco="A", numero="10")
    unidade2 = make_unidade(db_session, predio, bloco="A", numero="20")
    admin = make_user(db_session, email="admin.v3@test.local", role=RoleEnum.ADMINISTRADOR)
    client.post(
        "/veiculos",
        json={"unidade_id": unidade1.id, "placa": "AAA0001", "modelo": "Gol", "cor": "Branco"},
        headers=auth_header(admin),
    )
    client.post(
        "/veiculos",
        json={"unidade_id": unidade2.id, "placa": "BBB0002", "modelo": "Civic", "cor": "Preto"},
        headers=auth_header(admin),
    )

    dono = make_user(
        db_session,
        email="dono.v1@test.local",
        role=RoleEnum.PROPRIETARIO,
        predio=predio,
        unidades=[unidade1, unidade2],
    )
    response = client.get("/veiculos", headers=auth_header(dono))
    assert response.status_code == 200
    placas = {v["placa"] for v in response.json()}
    assert placas == {"AAA0001", "BBB0002"}


def test_soft_delete_veiculo(client, db_session):
    predio = make_predio(db_session)
    unidade = make_unidade(db_session, predio, bloco="C", numero="3")
    zelador = make_user(db_session, email="zelador.v2@test.local", role=RoleEnum.ZELADOR, predio=predio)
    criado = client.post(
        "/veiculos",
        json={"unidade_id": unidade.id, "placa": "CCC3333", "modelo": "HB20", "cor": "Vermelho"},
        headers=auth_header(zelador),
    ).json()

    response = client.delete(f"/veiculos/{criado['id']}", headers=auth_header(zelador))
    assert response.status_code == 204

    veiculo = db_session.get(Veiculo, criado["id"])
    db_session.refresh(veiculo)
    assert veiculo.deleted_at is not None

    listagem = client.get("/veiculos", headers=auth_header(zelador))
    ids = [v["id"] for v in listagem.json()]
    assert criado["id"] not in ids


def test_sindico_nao_acessa_veiculo_de_outro_predio(client, db_session):
    """Isolamento multi-tenant: um síndico não pode ver, editar ou apagar
    um veículo de outro prédio só adivinhando o id (regressão)."""
    predio_a = make_predio(db_session, nome="Predio A")
    unidade_a = make_unidade(db_session, predio_a)
    admin = make_user(db_session, email="admin.v9@test.local", role=RoleEnum.ADMINISTRADOR)
    veiculo_a = client.post(
        "/veiculos",
        json={"unidade_id": unidade_a.id, "placa": "AAA9001", "modelo": "Gol", "cor": "Branco"},
        headers=auth_header(admin),
    ).json()

    predio_b = make_predio(db_session, nome="Predio B")
    sindico_b = make_user(
        db_session, email="sindico.v9@test.local", role=RoleEnum.SINDICO, predio=predio_b
    )

    resposta_get = client.get(f"/veiculos/{veiculo_a['id']}", headers=auth_header(sindico_b))
    assert resposta_get.status_code == 404

    resposta_patch = client.patch(
        f"/veiculos/{veiculo_a['id']}", json={"cor": "Preto"}, headers=auth_header(sindico_b)
    )
    assert resposta_patch.status_code == 404

    resposta_delete = client.delete(f"/veiculos/{veiculo_a['id']}", headers=auth_header(sindico_b))
    assert resposta_delete.status_code == 404

    veiculo = db_session.get(Veiculo, veiculo_a["id"])
    db_session.refresh(veiculo)
    assert veiculo.deleted_at is None
    assert veiculo.cor == "Branco"
