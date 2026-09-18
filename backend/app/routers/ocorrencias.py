from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.models.enums import RoleEnum
from app.models.ocorrencia import Ocorrencia
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.ocorrencia import OcorrenciaAtualizar, OcorrenciaCreate, OcorrenciaRead

router = APIRouter(prefix="/ocorrencias", tags=["ocorrencias"])

# Quem edita QUALQUER ocorrência do prédio (spec: "editada pelo síndico em
# caso de necessidade") - o autor original não edita a própria depois de
# registrada, só a gestão corrige/complementa.
_PODE_EDITAR = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)
# Quem vê TODAS as ocorrências do prédio, não só as próprias - mesma
# privacidade de tickets (ver routers/tickets.py).
_GESTAO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO, RoleEnum.ZELADOR)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _ocorrencia_ou_404(db: Session, ocorrencia_id: int, current_user: Usuario) -> Ocorrencia:
    ocorrencia = db.get(Ocorrencia, ocorrencia_id)
    if ocorrencia is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ocorrência não encontrada.")
    if current_user.role != RoleEnum.ADMINISTRADOR and ocorrencia.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ocorrência não encontrada.")
    e_gestao = bool(current_user.roles_efetivos & set(_GESTAO))
    if not e_gestao and ocorrencia.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ocorrência não encontrada.")
    return ocorrencia


@router.post("", response_model=OcorrenciaRead, status_code=status.HTTP_201_CREATED)
def criar_ocorrencia(
    payload: OcorrenciaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> Ocorrencia:
    predio_id = resolver_predio_id(current_user, payload.predio_id)

    if payload.unidade_id is not None:
        unidade = db.get(Unidade, payload.unidade_id)
        if unidade is None or unidade.deleted_at is not None or unidade.predio_id != predio_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    ocorrencia = Ocorrencia(
        predio_id=predio_id,
        unidade_id=payload.unidade_id,
        titulo=payload.titulo,
        descricao=payload.descricao,
        created_by=current_user.id,
    )
    db.add(ocorrencia)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="livro_ocorrencias",
        entidade_id=ocorrencia.id,
        dados_depois=model_to_audit_dict(ocorrencia),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(ocorrencia)
    return ocorrencia


@router.get("", response_model=list[OcorrenciaRead])
def listar_ocorrencias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
) -> list[Ocorrencia]:
    query = db.query(Ocorrencia)

    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id is not None:
            query = query.filter(Ocorrencia.predio_id == predio_id)
    else:
        query = query.filter(Ocorrencia.predio_id == current_user.predio_id)
        if not (current_user.roles_efetivos & set(_GESTAO)):
            query = query.filter(Ocorrencia.created_by == current_user.id)

    return query.order_by(Ocorrencia.created_at.desc()).all()


@router.get("/{ocorrencia_id}", response_model=OcorrenciaRead)
def obter_ocorrencia(
    ocorrencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> Ocorrencia:
    return _ocorrencia_ou_404(db, ocorrencia_id, current_user)


@router.patch("/{ocorrencia_id}", response_model=OcorrenciaRead)
def atualizar_ocorrencia(
    ocorrencia_id: int,
    payload: OcorrenciaAtualizar,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_PODE_EDITAR)),
) -> Ocorrencia:
    ocorrencia = _ocorrencia_ou_404(db, ocorrencia_id, current_user)

    campos_enviados = payload.model_dump(exclude_unset=True)
    dados_antes = model_to_audit_dict(ocorrencia)
    for campo in ("titulo", "descricao"):
        if campo in campos_enviados:
            setattr(ocorrencia, campo, campos_enviados[campo])
    ocorrencia.editado_em = datetime.now(timezone.utc)
    ocorrencia.editado_por = current_user.id
    db.add(ocorrencia)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="livro_ocorrencias",
        entidade_id=ocorrencia.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(ocorrencia),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(ocorrencia)
    return ocorrencia
