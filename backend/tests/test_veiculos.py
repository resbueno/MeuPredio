from __future__ import annotations

from app.models.enums import RoleEnum
from app.models.log_auditoria import LogAuditoria
from app.models.unidade import Unidade
from app.models.veiculo import Veiculo
from tests.utils import auth_header, make_user


def _criar_unidade(db_session, *, bloco="A", numero="101") -> Unidade:
    unidade = Unidade(bloco=bloco, numero=numero)
    db_session.add(unidade)
    db_session.commit()
    db_session.refresh(unidade)
    return unidade


def test_criar_veiculo_sem_autenticacao_retorna_401(client, db_session):
    unidade = _criar_unidade(db_session)
    response = client.post(
        "/veiculos",
        json={"unidade_id": unidade.id, "placa": "ABC1D23", "modelo": "Onix", "cor": "Prata"},
    )
    assert response.status_code == 401


def test_morador_nao_pode_criar_veiculo(client, db_session):
    unidade = _criar_unidade(db_session)
    morador = make_user(
        db_session, email="morador.v1@test.local", role=RoleEnum.MORADOR, unidade_id=unidade.id
    )
    response = client.post(
        "/veiculos",
        json={"unidade_id": unidade.id, "placa": "ABC1D23", "modelo": "Onix", "cor": "Prata"},
        headers=auth_header(morador),
    )
    assert response.status_code == 403


def test_zelador_cria_veiculo_com_sucesso_e_normaliza_placa(client, db_session):
    unidade = _criar_unidade(db_session)
    zelador = make_user(db_session, email="zelador.v1@test.local", role=RoleEnum.ZELADOR)
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


def test_morador_ve_apenas_veiculos_da_propria_unidade(client, db_session):
    unidade1 = _criar_unidade(db_session, bloco="A", numero="1")
    unidade2 = _criar_unidade(db_session, bloco="B", numero="2")
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
        db_session, email="morador.v2@test.local", role=RoleEnum.MORADOR, unidade_id=unidade1.id
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


def test_soft_delete_veiculo(client, db_session):
    unidade = _criar_unidade(db_session, bloco="C", numero="3")
    zelador = make_user(db_session, email="zelador.v2@test.local", role=RoleEnum.ZELADOR)
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
