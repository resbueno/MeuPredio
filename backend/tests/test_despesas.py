from __future__ import annotations

from datetime import date, timedelta

from app.models.enums import RoleEnum
from app.models.fornecedor import Fornecedor
from app.models.log_auditoria import LogAuditoria
from app.models.predio import Predio
from app.models.usuario import Usuario
from tests.utils import auth_header, make_predio, make_user


def _admin_com_predio(db_session, *, email: str) -> tuple[Usuario, Predio]:
    admin = make_user(db_session, email=email, role=RoleEnum.ADMINISTRADOR)
    predio = make_predio(db_session)
    return admin, predio


def _criar_fornecedor(db_session, predio: Predio, *, nome="Fornecedor Teste", categoria="manutencao") -> Fornecedor:
    fornecedor = Fornecedor(predio_id=predio.id, nome=nome, categoria=categoria)
    db_session.add(fornecedor)
    db_session.commit()
    db_session.refresh(fornecedor)
    return fornecedor


def test_criar_despesa_sem_autenticacao_retorna_401(client):
    response = client.post(
        "/despesas",
        json={"descricao": "Conta de agua", "categoria": "agua", "valor": "150.00", "data_vencimento": "2026-10-10"},
    )
    assert response.status_code == 401


def test_morador_nao_pode_acessar_despesas(client, db_session):
    morador = make_user(db_session, email="morador.d1@test.local", role=RoleEnum.MORADOR)
    response = client.get("/despesas", headers=auth_header(morador))
    assert response.status_code == 403


def test_sindico_cria_despesa_pendente_com_sucesso(client, db_session):
    sindico = make_user(db_session, email="sindico.d1@test.local", role=RoleEnum.SINDICO)
    fornecedor = _criar_fornecedor(db_session, sindico.predio)

    response = client.post(
        "/despesas",
        json={
            "fornecedor_id": fornecedor.id,
            "descricao": "Manutencao do portao",
            "categoria": "manutencao",
            "valor": "450.5",
            "data_vencimento": "2026-10-15",
        },
        headers=auth_header(sindico),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pendente"
    assert body["valor"] == "450.50"
    assert body["esta_atrasada"] is False
    assert body["predio_id"] == sindico.predio_id

    log = (
        db_session.query(LogAuditoria)
        .filter(
            LogAuditoria.entidade == "despesas_lancamentos",
            LogAuditoria.entidade_id == body["id"],
            LogAuditoria.acao == "CREATE",
        )
        .one_or_none()
    )
    assert log is not None


def test_administrador_precisa_informar_predio_id(client, db_session):
    admin = make_user(db_session, email="admin.d0@test.local", role=RoleEnum.ADMINISTRADOR)
    response = client.post(
        "/despesas",
        json={"descricao": "Sem predio", "categoria": "outros", "valor": "10", "data_vencimento": "2026-10-15"},
        headers=auth_header(admin),
    )
    assert response.status_code == 422


def test_valor_zero_ou_negativo_e_rejeitado(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d1@test.local")
    response = client.post(
        "/despesas",
        json={
            "descricao": "Despesa invalida",
            "categoria": "outros",
            "valor": "0",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    )
    assert response.status_code == 422


def test_fornecedor_inexistente_retorna_404(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d2@test.local")
    response = client.post(
        "/despesas",
        json={
            "fornecedor_id": 999999,
            "descricao": "Despesa X",
            "categoria": "outros",
            "valor": "100",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    )
    assert response.status_code == 404


def test_fornecedor_de_outro_predio_retorna_404(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d9@test.local")
    outro_predio = make_predio(db_session)
    fornecedor_alheio = _criar_fornecedor(db_session, outro_predio)

    response = client.post(
        "/despesas",
        json={
            "fornecedor_id": fornecedor_alheio.id,
            "descricao": "Despesa X",
            "categoria": "outros",
            "valor": "100",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    )
    assert response.status_code == 404


def test_despesa_vencida_aparece_como_atrasada(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d3@test.local")
    ontem = (date.today() - timedelta(days=1)).isoformat()
    response = client.post(
        "/despesas",
        json={
            "descricao": "Conta vencida",
            "categoria": "luz",
            "valor": "200",
            "data_vencimento": ontem,
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    )
    assert response.json()["esta_atrasada"] is True


def test_registrar_pagamento_muda_status_e_bloqueia_dupla_baixa(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d4@test.local")
    criada = client.post(
        "/despesas",
        json={
            "descricao": "Agua",
            "categoria": "agua",
            "valor": "300",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()

    pago = client.post(f"/despesas/{criada['id']}/pagar", json={}, headers=auth_header(admin))
    assert pago.status_code == 200
    assert pago.json()["status"] == "pago"
    assert pago.json()["data_pagamento"] is not None

    segunda_baixa = client.post(f"/despesas/{criada['id']}/pagar", json={}, headers=auth_header(admin))
    assert segunda_baixa.status_code == 409


def test_nao_pode_editar_despesa_ja_paga(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d5@test.local")
    criada = client.post(
        "/despesas",
        json={
            "descricao": "Gas",
            "categoria": "gas",
            "valor": "80",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()
    client.post(f"/despesas/{criada['id']}/pagar", json={}, headers=auth_header(admin))

    resposta = client.patch(
        f"/despesas/{criada['id']}", json={"valor": "999"}, headers=auth_header(admin)
    )
    assert resposta.status_code == 409


def test_anexar_comprovante_em_despesa_paga(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d12@test.local")
    criada = client.post(
        "/despesas",
        json={
            "descricao": "Gas",
            "categoria": "gas",
            "valor": "80",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()
    client.post(f"/despesas/{criada['id']}/pagar", json={}, headers=auth_header(admin))

    resposta = client.post(
        f"/despesas/{criada['id']}/comprovante",
        files={"arquivo": ("comprovante.jpg", b"fake-bytes", "image/jpeg")},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 200
    assert resposta.json()["comprovante_pagamento_url"] is not None


def test_nao_pode_anexar_comprovante_em_despesa_pendente(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d13@test.local")
    criada = client.post(
        "/despesas",
        json={
            "descricao": "Gas",
            "categoria": "gas",
            "valor": "80",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()

    resposta = client.post(
        f"/despesas/{criada['id']}/comprovante",
        files={"arquivo": ("comprovante.jpg", b"fake-bytes", "image/jpeg")},
        headers=auth_header(admin),
    )
    assert resposta.status_code == 409


def test_desfazer_pagamento_limpa_comprovante(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d14@test.local")
    criada = client.post(
        "/despesas",
        json={
            "descricao": "Gas",
            "categoria": "gas",
            "valor": "80",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()
    client.post(f"/despesas/{criada['id']}/pagar", json={}, headers=auth_header(admin))
    client.post(
        f"/despesas/{criada['id']}/comprovante",
        files={"arquivo": ("comprovante.jpg", b"fake-bytes", "image/jpeg")},
        headers=auth_header(admin),
    )

    desfeito = client.post(f"/despesas/{criada['id']}/desfazer-pagamento", headers=auth_header(admin))
    assert desfeito.json()["comprovante_pagamento_url"] is None


def test_desfazer_pagamento_volta_para_pendente_e_libera_edicao(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d10@test.local")
    criada = client.post(
        "/despesas",
        json={
            "descricao": "Gas",
            "categoria": "gas",
            "valor": "80",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()
    client.post(f"/despesas/{criada['id']}/pagar", json={}, headers=auth_header(admin))

    desfeito = client.post(f"/despesas/{criada['id']}/desfazer-pagamento", headers=auth_header(admin))
    assert desfeito.status_code == 200
    assert desfeito.json()["status"] == "pendente"
    assert desfeito.json()["data_pagamento"] is None

    edicao = client.patch(
        f"/despesas/{criada['id']}", json={"valor": "999"}, headers=auth_header(admin)
    )
    assert edicao.status_code == 200
    assert edicao.json()["valor"] == "999.00"


def test_desfazer_pagamento_de_despesa_pendente_retorna_409(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d11@test.local")
    criada = client.post(
        "/despesas",
        json={
            "descricao": "Gas",
            "categoria": "gas",
            "valor": "80",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()

    resposta = client.post(f"/despesas/{criada['id']}/desfazer-pagamento", headers=auth_header(admin))
    assert resposta.status_code == 409


def test_cancelar_despesa(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d6@test.local")
    criada = client.post(
        "/despesas",
        json={
            "descricao": "Servico cancelado",
            "categoria": "outros",
            "valor": "50",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()

    resposta = client.post(f"/despesas/{criada['id']}/cancelar", headers=auth_header(admin))
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "cancelado"


def test_filtrar_por_status(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d7@test.local")
    pendente = client.post(
        "/despesas",
        json={
            "descricao": "Pendente",
            "categoria": "outros",
            "valor": "10",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()
    paga = client.post(
        "/despesas",
        json={
            "descricao": "Paga",
            "categoria": "outros",
            "valor": "20",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()
    client.post(f"/despesas/{paga['id']}/pagar", json={}, headers=auth_header(admin))

    resposta = client.get(
        "/despesas", params={"status": "pendente", "predio_id": predio.id}, headers=auth_header(admin)
    )
    ids = [d["id"] for d in resposta.json()]
    assert pendente["id"] in ids
    assert paga["id"] not in ids


def test_sindico_nao_ve_despesa_de_outro_predio(client, db_session):
    admin, outro_predio = _admin_com_predio(db_session, email="admin.d10@test.local")
    despesa_alheia = client.post(
        "/despesas",
        json={
            "descricao": "Alheia",
            "categoria": "outros",
            "valor": "10",
            "data_vencimento": "2026-10-15",
            "predio_id": outro_predio.id,
        },
        headers=auth_header(admin),
    ).json()
    sindico = make_user(db_session, email="sindico.d2@test.local", role=RoleEnum.SINDICO)

    resposta = client.get(f"/despesas/{despesa_alheia['id']}", headers=auth_header(sindico))
    assert resposta.status_code == 404


def test_soft_delete_despesa(client, db_session):
    admin, predio = _admin_com_predio(db_session, email="admin.d8@test.local")
    criada = client.post(
        "/despesas",
        json={
            "descricao": "A remover",
            "categoria": "outros",
            "valor": "10",
            "data_vencimento": "2026-10-15",
            "predio_id": predio.id,
        },
        headers=auth_header(admin),
    ).json()

    resposta = client.delete(f"/despesas/{criada['id']}", headers=auth_header(admin))
    assert resposta.status_code == 204

    listagem = client.get("/despesas", params={"predio_id": predio.id}, headers=auth_header(admin))
    assert criada["id"] not in [d["id"] for d in listagem.json()]
