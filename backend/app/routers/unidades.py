from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_current_user, get_db, require_role
from app.models.enums import RoleEnum
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.unidade import UnidadeCreate, UnidadeRead, UnidadeUpdate

router = APIRouter(prefix="/unidades", tags=["unidades"])

_GESTORES = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _unidade_ou_404(db: Session, unidade_id: int) -> Unidade:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade nao encontrada.")
    return unidade


def _validar_proprietario(db: Session, proprietario_id: int | None) -> None:
    if proprietario_id is None:
        return
    proprietario = db.get(Usuario, proprietario_id)
    if proprietario is None or proprietario.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario informado como proprietario nao foi encontrado.",
        )


@router.post("", response_model=UnidadeRead, status_code=status.HTTP_201_CREATED)
def criar_unidade(
    payload: UnidadeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTORES)),
) -> Unidade:
    _validar_proprietario(db, payload.proprietario_id)

    unidade = Unidade(
        bloco=payload.bloco,
        numero=payload.numero,
        proprietario_id=payload.proprietario_id,
        created_by=current_user.id,
    )
    db.add(unidade)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe uma unidade com este bloco e numero.",
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


@router.get("", response_model=list[UnidadeRead])
def listar_unidades(
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
    incluir_inativos: bool = False,
) -> list[Unidade]:
    query = db.query(Unidade)
    if not incluir_inativos:
        query = query.filter(Unidade.deleted_at.is_(None))
    return query.order_by(Unidade.bloco, Unidade.numero).all()


@router.get("/{unidade_id}", response_model=UnidadeRead)
def obter_unidade(
    unidade_id: int,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
) -> Unidade:
    return _unidade_ou_404(db, unidade_id)


@router.patch("/{unidade_id}", response_model=UnidadeRead)
def atualizar_unidade(
    unidade_id: int,
    payload: UnidadeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTORES)),
) -> Unidade:
    unidade = _unidade_ou_404(db, unidade_id)
    campos_enviados = payload.model_dump(exclude_unset=True)

    if "proprietario_id" in campos_enviados:
        _validar_proprietario(db, campos_enviados["proprietario_id"])

    dados_antes = model_to_audit_dict(unidade)

    if "bloco" in campos_enviados:
        unidade.bloco = campos_enviados["bloco"]
    if "numero" in campos_enviados:
        unidade.numero = campos_enviados["numero"]
    if "proprietario_id" in campos_enviados:
        unidade.proprietario_id = campos_enviados["proprietario_id"]

    db.add(unidade)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe uma unidade com este bloco e numero.",
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
