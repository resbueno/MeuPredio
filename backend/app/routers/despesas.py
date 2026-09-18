from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.crypto import decrypt_secret
from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.core.groq_ocr import GroqIndisponivelError, extrair_dados_boleto
from app.core.pdf import PdfInvalidoError, primeira_pagina_como_png
from app.core.rateio import calcular_rateio
from app.core.storage import caminho_documento, salvar_documento
from app.models.despesa_lancamento import DespesaLancamento
from app.models.enums import CriterioRateioEnum, RoleEnum, StatusDespesaEnum
from app.models.fornecedor import Fornecedor
from app.models.predio import Predio
from app.models.rateio_despesa_item import RateioDespesaItem
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.despesa_lancamento import (
    DespesaLancamentoCreate,
    DespesaLancamentoRead,
    DespesaLancamentoRegistrarPagamento,
    DespesaLancamentoUpdate,
)
from app.schemas.ocr import ExtracaoBoletoResponse
from app.schemas.rateio import RatearDespesaRequest

router = APIRouter(prefix="/despesas", tags=["despesas"])

# Mesmo escopo de acesso de fornecedores.py: motor financeiro restrito a
# síndico/administrador nesta fatia da Fase 2 (ver comentário lá).
_FINANCEIRO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)

# PDF é aceito no upload, mas o modelo com visão do Groq (core/groq_ocr.py)
# só aceita imagem - a primeira página do PDF é convertida para PNG antes de
# ir para a IA (ver core/pdf.py); o arquivo original (PDF) é o que fica
# salvo em disco/documento_url.
_MIME_TYPES_OCR_PERMITIDOS = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
_TAMANHO_MAXIMO_OCR_BYTES = 10 * 1024 * 1024


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _despesa_ou_404(db: Session, despesa_id: int, current_user: Usuario) -> DespesaLancamento:
    despesa = db.get(DespesaLancamento, despesa_id)
    if despesa is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa nao encontrada.")
    # Isolamento multi-tenant: síndico nunca acessa despesa de outro prédio,
    # nem por id direto (some como 404, não confirma existência).
    if current_user.role != RoleEnum.ADMINISTRADOR and despesa.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa nao encontrada.")
    return despesa


def _validar_fornecedor(db: Session, fornecedor_id: int | None, predio_id: int) -> None:
    if fornecedor_id is None:
        return
    fornecedor = db.get(Fornecedor, fornecedor_id)
    if (
        fornecedor is None
        or fornecedor.deleted_at is not None
        or fornecedor.predio_id != predio_id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor nao encontrado.")


def _exigir_pendente(despesa: DespesaLancamento, acao: str) -> None:
    if despesa.status != StatusDespesaEnum.PENDENTE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"So e possivel {acao} um lancamento pendente (status atual: {despesa.status.value}).",
        )


def _exigir_pago(despesa: DespesaLancamento, acao: str) -> None:
    if despesa.status != StatusDespesaEnum.PAGO:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"So e possivel {acao} um lancamento pago (status atual: {despesa.status.value}).",
        )


@router.post("", response_model=DespesaLancamentoRead, status_code=status.HTTP_201_CREATED)
def criar_despesa(
    payload: DespesaLancamentoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    predio_id = resolver_predio_id(current_user, payload.predio_id)
    _validar_fornecedor(db, payload.fornecedor_id, predio_id)

    despesa = DespesaLancamento(
        predio_id=predio_id,
        fornecedor_id=payload.fornecedor_id,
        descricao=payload.descricao,
        categoria=payload.categoria,
        valor=payload.valor,
        data_vencimento=payload.data_vencimento,
        observacoes=payload.observacoes,
        documento_url=payload.documento_url,
        status=StatusDespesaEnum.PENDENTE,
        created_by=current_user.id,
    )
    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa


@router.post("/ocr/extrair", response_model=ExtracaoBoletoResponse)
async def extrair_boleto(
    request: Request,
    arquivo: UploadFile = File(...),
    predio_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> ExtracaoBoletoResponse:
    """Envia um boleto/comprovante (imagem ou PDF) para extração via Groq.

    Não cria a despesa: devolve os campos extraídos (com `documento_url`)
    para o chamador revisar/corrigir e então chamar `POST /despesas`
    normalmente - "Validação Dinâmica" do roadmap, nunca confia cegamente no
    que a IA leu de um documento financeiro.
    """
    predio_id_resolvido = resolver_predio_id(current_user, predio_id)
    predio = db.get(Predio, predio_id_resolvido)
    if predio is None or predio.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Predio nao encontrado.")
    if not predio.groq_api_key_cifrada:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Este predio ainda nao tem a integracao de OCR (Groq) configurada "
                "(ver PUT /predios/{predio_id}/integracao-ocr)."
            ),
        )

    if arquivo.content_type not in _MIME_TYPES_OCR_PERMITIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Tipo de arquivo nao suportado. Envie uma imagem (JPEG/PNG/WEBP) ou PDF.",
        )

    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Arquivo vazio.")
    if len(conteudo) > _TAMANHO_MAXIMO_OCR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Arquivo maior que o limite permitido (10MB).",
        )

    documento_url = salvar_documento(predio_id_resolvido, arquivo.filename or "documento", conteudo)

    conteudo_para_ocr, mime_type_para_ocr = conteudo, arquivo.content_type
    if arquivo.content_type == "application/pdf":
        try:
            conteudo_para_ocr = primeira_pagina_como_png(conteudo)
        except PdfInvalidoError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
            ) from exc
        mime_type_para_ocr = "image/png"

    try:
        extraido = extrair_dados_boleto(
            api_key=decrypt_secret(predio.groq_api_key_cifrada),
            conteudo=conteudo_para_ocr,
            mime_type=mime_type_para_ocr,
        )
    except GroqIndisponivelError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="OCR_EXTRACAO",
        entidade="despesas_lancamentos",
        entidade_id=None,
        dados_depois={"predio_id": predio_id_resolvido, "documento_url": documento_url},
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()

    return ExtracaoBoletoResponse(documento_url=documento_url, **extraido.model_dump())


@router.get("/documentos/{predio_id}/{nome_arquivo}")
def obter_documento(
    predio_id: int,
    nome_arquivo: str,
    # Qualquer papel autenticado (nao so _FINANCEIRO): o Portal da
    # Transparencia deixa qualquer condomino ver o comprovante/boleto
    # digitalizado - o escopo por predio abaixo e a guarda real.
    current_user: Usuario = Depends(require_role()),
) -> FileResponse:
    if current_user.role != RoleEnum.ADMINISTRADOR and current_user.predio_id != predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento nao encontrado.")

    caminho = caminho_documento(predio_id, nome_arquivo)
    if caminho is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento nao encontrado.")
    return FileResponse(caminho)


@router.get("", response_model=list[DespesaLancamentoRead])
def listar_despesas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
    predio_id: int | None = None,
    status_: StatusDespesaEnum | None = Query(default=None, alias="status"),
    categoria: str | None = None,
    fornecedor_id: int | None = None,
    incluir_inativos: bool = False,
) -> list[DespesaLancamento]:
    query = db.query(DespesaLancamento)
    if not incluir_inativos:
        query = query.filter(DespesaLancamento.deleted_at.is_(None))
    if status_ is not None:
        query = query.filter(DespesaLancamento.status == status_)
    if categoria is not None:
        query = query.filter(DespesaLancamento.categoria == categoria)
    if fornecedor_id is not None:
        query = query.filter(DespesaLancamento.fornecedor_id == fornecedor_id)

    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id is not None:
            query = query.filter(DespesaLancamento.predio_id == predio_id)
    else:
        query = query.filter(DespesaLancamento.predio_id == current_user.predio_id)

    return query.order_by(DespesaLancamento.data_vencimento).all()


@router.get("/{despesa_id}", response_model=DespesaLancamentoRead)
def obter_despesa(
    despesa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    return _despesa_ou_404(db, despesa_id, current_user)


@router.patch("/{despesa_id}", response_model=DespesaLancamentoRead)
def atualizar_despesa(
    despesa_id: int,
    payload: DespesaLancamentoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    despesa = _despesa_ou_404(db, despesa_id, current_user)
    _exigir_pendente(despesa, "editar")
    campos_enviados = payload.model_dump(exclude_unset=True)

    if "fornecedor_id" in campos_enviados:
        _validar_fornecedor(db, campos_enviados["fornecedor_id"], despesa.predio_id)

    dados_antes = model_to_audit_dict(despesa)

    for campo in (
        "fornecedor_id",
        "descricao",
        "categoria",
        "valor",
        "data_vencimento",
        "observacoes",
        "documento_url",
    ):
        if campo in campos_enviados:
            setattr(despesa, campo, campos_enviados[campo])

    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa


@router.post("/{despesa_id}/ratear", response_model=DespesaLancamentoRead)
def ratear_despesa(
    despesa_id: int,
    payload: RatearDespesaRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    """Divide o valor da despesa entre as unidades ativas do prédio.

    Chamar de novo (com o mesmo critério ou outro) RECALCULA do zero: o
    conjunto de itens anterior é substituído, nunca acumulado — só faz
    sentido em uma despesa ainda pendente (mesma regra de `atualizar_despesa`),
    então mudar de ideia sobre o critério antes de pagar é seguro.
    """
    despesa = _despesa_ou_404(db, despesa_id, current_user)
    _exigir_pendente(despesa, "ratear")

    unidades = (
        db.query(Unidade)
        .filter(Unidade.predio_id == despesa.predio_id, Unidade.deleted_at.is_(None))
        .order_by(Unidade.id)
        .all()
    )
    if not unidades:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nenhuma unidade ativa neste predio para ratear.",
        )

    if payload.criterio == CriterioRateioEnum.FRACAO_IDEAL:
        sem_fracao = [u.id for u in unidades if not u.fracao_ideal or u.fracao_ideal <= 0]
        if sem_fracao:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "Todas as unidades ativas precisam ter fracao_ideal definida (>0) "
                    f"para ratear por fracao ideal. Unidade(s) sem fracao_ideal: {sem_fracao}."
                ),
            )
        pesos = [(u.id, u.fracao_ideal) for u in unidades]
    else:
        pesos = [(u.id, Decimal(1)) for u in unidades]

    valores_por_unidade = calcular_rateio(despesa.valor, pesos)

    db.query(RateioDespesaItem).filter(
        RateioDespesaItem.despesa_lancamento_id == despesa.id
    ).delete(synchronize_session=False)

    itens_novos = []
    for unidade_id, valor_unidade in valores_por_unidade.items():
        item = RateioDespesaItem(
            predio_id=despesa.predio_id,
            despesa_lancamento_id=despesa.id,
            unidade_id=unidade_id,
            valor=valor_unidade,
            criterio=payload.criterio,
            created_by=current_user.id,
        )
        db.add(item)
        itens_novos.append(item)

    despesa.rateado_em = datetime.now(timezone.utc)
    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="RATEIO",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_depois={
            "criterio": payload.criterio.value,
            "itens": [
                {"unidade_id": item.unidade_id, "valor": float(item.valor)} for item in itens_novos
            ],
        },
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa


@router.post("/{despesa_id}/pagar", response_model=DespesaLancamentoRead)
def registrar_pagamento(
    despesa_id: int,
    payload: DespesaLancamentoRegistrarPagamento,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    despesa = _despesa_ou_404(db, despesa_id, current_user)
    _exigir_pendente(despesa, "dar baixa em")

    dados_antes = model_to_audit_dict(despesa)
    despesa.status = StatusDespesaEnum.PAGO
    despesa.data_pagamento = payload.data_pagamento
    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa


@router.post("/{despesa_id}/desfazer-pagamento", response_model=DespesaLancamentoRead)
def desfazer_pagamento(
    despesa_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    """Reverte a baixa de um lancamento pago, voltando para pendente.

    Existe porque o PATCH de edicao so aceita lancamento pendente
    (`_exigir_pendente`) - marcar como paga por engano (ou precisar corrigir
    um dado depois da baixa) nao pode virar um beco sem saida.
    """
    despesa = _despesa_ou_404(db, despesa_id, current_user)
    _exigir_pago(despesa, "desfazer o pagamento de")

    dados_antes = model_to_audit_dict(despesa)
    despesa.status = StatusDespesaEnum.PENDENTE
    despesa.data_pagamento = None
    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa


@router.post("/{despesa_id}/cancelar", response_model=DespesaLancamentoRead)
def cancelar_despesa(
    despesa_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> DespesaLancamento:
    despesa = _despesa_ou_404(db, despesa_id, current_user)
    _exigir_pendente(despesa, "cancelar")

    dados_antes = model_to_audit_dict(despesa)
    despesa.status = StatusDespesaEnum.CANCELADO
    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(despesa)
    return despesa


@router.delete("/{despesa_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_despesa(
    despesa_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> None:
    despesa = _despesa_ou_404(db, despesa_id, current_user)
    if despesa.deleted_at is not None:
        return None

    dados_antes = model_to_audit_dict(despesa)
    despesa.deleted_at = datetime.now(timezone.utc)
    db.add(despesa)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="SOFT_DELETE",
        entidade="despesas_lancamentos",
        entidade_id=despesa.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(despesa),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None
