from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_db, require_role
from app.core.rateio_despesa import aplicar_rateio
from app.models.despesa_lancamento import DespesaLancamento
from app.models.enums import CriterioRateioEnum, RoleEnum, StatusDespesaEnum
from app.models.prestador_servico import PrestadorServico
from app.models.usuario import Usuario
from app.schemas.despesa_lancamento import DespesaLancamentoRead
from app.schemas.prestador_servico import (
    PrestadorServicoAtualizar,
    PrestadorServicoCreate,
    PrestadorServicoLancarCusto,
    PrestadorServicoRead,
)

router = APIRouter(prefix="/prestadores-servico", tags=["prestadores-servico"])

# Cadastro e consulta: síndico e zelador (o administrador global fica de fora
# por decisão explícita do produto). Já LANÇAR o custo - que cria uma despesa
# e, se marcado, cobra as unidades - é decisão financeira: só o síndico.
_EQUIPE = (RoleEnum.SINDICO, RoleEnum.ZELADOR)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _prestador_ou_404(db: Session, prestador_id: int, current_user: Usuario) -> PrestadorServico:
    prestador = db.get(PrestadorServico, prestador_id)
    if (
        prestador is None
        or prestador.deleted_at is not None
        or prestador.predio_id != current_user.predio_id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prestador não encontrado.")
    return prestador


@router.post("", response_model=PrestadorServicoRead, status_code=status.HTTP_201_CREATED)
def criar_prestador(
    payload: PrestadorServicoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EQUIPE)),
) -> PrestadorServico:
    dados = payload.model_dump()
    dados["criterio_rateio"] = payload.criterio_rateio.value
    prestador = PrestadorServico(predio_id=current_user.predio_id, created_by=current_user.id, **dados)
    db.add(prestador)
    db.flush()
    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="prestadores_servico",
        entidade_id=prestador.id,
        dados_depois=model_to_audit_dict(prestador),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(prestador)
    return prestador


@router.get("", response_model=list[PrestadorServicoRead])
def listar_prestadores(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EQUIPE)),
    incluir_inativos: bool = False,
) -> list[PrestadorServico]:
    query = db.query(PrestadorServico).filter(
        PrestadorServico.predio_id == current_user.predio_id,
        PrestadorServico.deleted_at.is_(None),
    )
    if not incluir_inativos:
        query = query.filter(PrestadorServico.ativo.is_(True))
    return query.order_by(PrestadorServico.nome.asc()).all()


@router.patch("/{prestador_id}", response_model=PrestadorServicoRead)
def atualizar_prestador(
    prestador_id: int,
    payload: PrestadorServicoAtualizar,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EQUIPE)),
) -> PrestadorServico:
    prestador = _prestador_ou_404(db, prestador_id, current_user)
    dados_antes = model_to_audit_dict(prestador)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        if campo == "criterio_rateio" and valor is not None:
            valor = valor.value
        setattr(prestador, campo, valor)
    db.add(prestador)
    db.flush()
    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="prestadores_servico",
        entidade_id=prestador.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(prestador),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(prestador)
    return prestador


@router.delete("/{prestador_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_prestador(
    prestador_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EQUIPE)),
) -> None:
    prestador = _prestador_ou_404(db, prestador_id, current_user)
    dados_antes = model_to_audit_dict(prestador)
    prestador.deleted_at = datetime.now(timezone.utc)
    db.add(prestador)
    db.flush()
    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="SOFT_DELETE",
        entidade="prestadores_servico",
        entidade_id=prestador.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(prestador),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None


@router.get("/{prestador_id}/lancamentos", response_model=list[DespesaLancamentoRead])
def listar_lancamentos_do_prestador(
    prestador_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EQUIPE)),
) -> list[DespesaLancamento]:
    prestador = _prestador_ou_404(db, prestador_id, current_user)
    return (
        db.query(DespesaLancamento)
        .filter(
            DespesaLancamento.prestador_servico_id == prestador.id,
            DespesaLancamento.deleted_at.is_(None),
        )
        .order_by(DespesaLancamento.data_vencimento.desc())
        .all()
    )


@router.post(
    "/{prestador_id}/lancar-custo",
    response_model=DespesaLancamentoRead,
    status_code=status.HTTP_201_CREATED,
)
def lancar_custo(
    prestador_id: int,
    payload: PrestadorServicoLancarCusto,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.SINDICO)),
) -> DespesaLancamento:
    """Lança o custo mensal do prestador como despesa do condomínio - e, se
    `incluir_no_rateio`, já rateia entre as unidades pelo critério
    configurado. Um lançamento (não cancelado) por prestador por mês."""
    prestador = _prestador_ou_404(db, prestador_id, current_user)
    if not prestador.ativo:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este prestador está inativo.")
    if prestador.custo_mensal <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Defina um custo mensal maior que zero para lançar.",
        )

    inicio_mes = payload.data_vencimento.replace(day=1)
    proximo_mes = (
        date(inicio_mes.year + 1, 1, 1)
        if inicio_mes.month == 12
        else date(inicio_mes.year, inicio_mes.month + 1, 1)
    )
    ja_lancado = (
        db.query(DespesaLancamento)
        .filter(
            DespesaLancamento.prestador_servico_id == prestador.id,
            DespesaLancamento.deleted_at.is_(None),
            DespesaLancamento.status != StatusDespesaEnum.CANCELADO,
            DespesaLancamento.data_vencimento >= inicio_mes,
            DespesaLancamento.data_vencimento < proximo_mes,
        )
        .first()
    )
    if ja_lancado is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="O custo deste prestador já foi lançado para este mês.",
        )

    despesa = DespesaLancamento(
        predio_id=prestador.predio_id,
        prestador_servico_id=prestador.id,
        descricao=f"{prestador.nome} - {prestador.tipo_servico}",
        categoria=prestador.tipo_servico,
        valor=prestador.custo_mensal,
        data_vencimento=payload.data_vencimento,
        observacoes=payload.observacoes,
        status=StatusDespesaEnum.PENDENTE,
        created_by=current_user.id,
    )
    db.add(despesa)
    db.flush()

    itens = []
    if prestador.incluir_no_rateio:
        itens = aplicar_rateio(db, despesa, CriterioRateioEnum(prestador.criterio_rateio), current_user.id)

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_depois={
            **model_to_audit_dict(despesa),
            "origem": "prestador_servico",
            "rateado": bool(itens),
        },
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa
