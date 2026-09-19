from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_current_user, get_db, require_role, resolver_predio_id
from app.models.enums import RoleEnum
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.unidade import UnidadeCreate, UnidadeLoteCreate, UnidadeRead, UnidadeUpdate

router = APIRouter(prefix="/unidades", tags=["unidades"])

_GESTORES = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _unidade_ou_404(db: Session, unidade_id: int) -> Unidade:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")
    return unidade


def _autorizar_mesmo_predio(current_user: Usuario, unidade: Unidade) -> None:
    """Isolamento multi-tenant: ninguém enxerga/mexe em unidade de outro
    prédio - nem por acesso direto via id (some como 404, não 403, para não
    confirmar que a unidade existe em outro tenant). Administrador (sem
    prédio) não tem essa restrição."""
    if current_user.role == RoleEnum.ADMINISTRADOR:
        return
    if current_user.predio_id != unidade.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")


@router.post("", response_model=UnidadeRead, status_code=status.HTTP_201_CREATED)
def criar_unidade(
    payload: UnidadeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTORES)),
) -> Unidade:
    predio_id = resolver_predio_id(current_user, payload.predio_id)

    unidade = Unidade(
        predio_id=predio_id,
        bloco=payload.bloco,
        numero=payload.numero,
        fracao_ideal=payload.fracao_ideal,
        vaga=payload.vaga,
        created_by=current_user.id,
    )
    db.add(unidade)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma unidade com este bloco e número neste prédio.",
        ) from None

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="unidades",
        entidade_id=unidade.id,
        dados_depois=model_to_audit_dict(unidade),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(unidade)
    return unidade


@router.post("/lote", response_model=list[UnidadeRead], status_code=status.HTTP_201_CREATED)
def criar_unidades_em_lote(
    payload: UnidadeLoteCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTORES)),
) -> list[Unidade]:
    """Cria várias unidades de uma vez (ex.: um bloco inteiro) - tudo ou
    nada: se alguma combinação bloco/número já existir (ou se repetir
    dentro do próprio lote), nada é criado."""
    predio_id = resolver_predio_id(current_user, payload.predio_id)

    combinacoes = {(item.bloco, item.numero) for item in payload.unidades}
    if len(combinacoes) != len(payload.unidades):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="O lote tem bloco/número repetido dentro dele mesmo.",
        )

    unidades = [
        Unidade(
            predio_id=predio_id,
            bloco=item.bloco,
            numero=item.numero,
            fracao_ideal=item.fracao_ideal,
            vaga=item.vaga,
            created_by=current_user.id,
        )
        for item in payload.unidades
    ]
    db.add_all(unidades)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Uma ou mais unidades do lote já existem neste prédio (bloco/número duplicado).",
        ) from None

    for unidade in unidades:
        registrar_log(
            db,
            usuario_id=current_user.id,
            acao="CREATE",
            entidade="unidades",
            entidade_id=unidade.id,
            dados_depois=model_to_audit_dict(unidade),
            ip_origem=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    db.commit()
    for unidade in unidades:
        db.refresh(unidade)
    return unidades


@router.get("", response_model=list[UnidadeRead])
def listar_unidades(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    predio_id: int | None = None,
    incluir_inativos: bool = False,
) -> list[Unidade]:
    query = db.query(Unidade)
    if not incluir_inativos:
        query = query.filter(Unidade.deleted_at.is_(None))

    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id is not None:
            query = query.filter(Unidade.predio_id == predio_id)
    else:
        # Qualquer papel vinculado a um prédio só enxerga as unidades DAQUELE
        # prédio, ignorando qualquer predio_id que tente passar via query.
        query = query.filter(Unidade.predio_id == current_user.predio_id)

    return query.order_by(Unidade.bloco, Unidade.numero).all()


@router.get("/{unidade_id}", response_model=UnidadeRead)
def obter_unidade(
    unidade_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Unidade:
    unidade = _unidade_ou_404(db, unidade_id)
    _autorizar_mesmo_predio(current_user, unidade)
    return unidade


@router.patch("/{unidade_id}", response_model=UnidadeRead)
def atualizar_unidade(
    unidade_id: int,
    payload: UnidadeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTORES)),
) -> Unidade:
    unidade = _unidade_ou_404(db, unidade_id)
    _autorizar_mesmo_predio(current_user, unidade)
    campos_enviados = payload.model_dump(exclude_unset=True)

    dados_antes = model_to_audit_dict(unidade)

    if "bloco" in campos_enviados:
        unidade.bloco = campos_enviados["bloco"]
    if "numero" in campos_enviados:
        unidade.numero = campos_enviados["numero"]
    if "fracao_ideal" in campos_enviados:
        unidade.fracao_ideal = campos_enviados["fracao_ideal"]
    if "vaga" in campos_enviados:
        unidade.vaga = campos_enviados["vaga"]

    db.add(unidade)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma unidade com este bloco e número neste prédio.",
        ) from None

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="unidades",
        entidade_id=unidade.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(unidade),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(unidade)
    return unidade


@router.delete("/{unidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_unidade(
    unidade_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTORES)),
) -> None:
    unidade = _unidade_ou_404(db, unidade_id)
    _autorizar_mesmo_predio(current_user, unidade)
    if unidade.deleted_at is not None:
        return None

    dados_antes = model_to_audit_dict(unidade)
    unidade.deleted_at = datetime.now(timezone.utc)
    db.add(unidade)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="SOFT_DELETE",
        entidade="unidades",
        entidade_id=unidade.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(unidade),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None
