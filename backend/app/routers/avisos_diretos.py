from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.models.aviso_direto import AvisoDireto
from app.models.despesa_lancamento import DespesaLancamento
from app.models.enums import DestinatarioAvisoEnum, RoleEnum, StatusDespesaEnum, TipoAvisoDiretoEnum
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.aviso_direto import AvisoDiretoCreate, AvisoDiretoRead, AvisoDiretoResponder

router = APIRouter(prefix="/avisos-diretos", tags=["avisos-diretos"])

# So sindico/administrador emite aviso direto (aviso, advertencia ou
# multa) - nunca o zelador, nunca o proprio morador para si mesmo.
_EMISSORES = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _destinatario_bate_com_algum_papel(
    destinatario: DestinatarioAvisoEnum, roles: set[RoleEnum]
) -> bool:
    """`roles` são os `roles_efetivos` do usuário (papel principal + extras)
    - basta UM bater, já que a mesma pessoa pode acumular papéis (ex.: ser
    morador E proprietário da mesma unidade)."""
    if destinatario == DestinatarioAvisoEnum.AMBOS:
        return bool(roles & {RoleEnum.MORADOR, RoleEnum.PROPRIETARIO})
    return any(role.value == destinatario.value for role in roles)


def _pode_ver(aviso: AvisoDireto, current_user: Usuario) -> bool:
    if current_user.roles_efetivos & set(_EMISSORES):
        return True
    unidade_ids = {u.id for u in current_user.unidades}
    return aviso.unidade_id in unidade_ids and _destinatario_bate_com_algum_papel(
        aviso.destinatario, current_user.roles_efetivos
    )


def _aviso_ou_404(db: Session, aviso_id: int, current_user: Usuario) -> AvisoDireto:
    aviso = db.get(AvisoDireto, aviso_id)
    if aviso is None or aviso.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso não encontrado.")
    if current_user.role != RoleEnum.ADMINISTRADOR and aviso.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso não encontrado.")
    if not _pode_ver(aviso, current_user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aviso não encontrado.")
    return aviso


@router.post("", response_model=AvisoDiretoRead, status_code=status.HTTP_201_CREATED)
def criar_aviso_direto(
    payload: AvisoDiretoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EMISSORES)),
) -> AvisoDireto:
    predio_id = resolver_predio_id(current_user, payload.predio_id)

    unidade = db.get(Unidade, payload.unidade_id)
    if unidade is None or unidade.deleted_at is not None or unidade.predio_id != predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    aviso = AvisoDireto(
        predio_id=predio_id,
        unidade_id=payload.unidade_id,
        destinatario=payload.destinatario,
        tipo=payload.tipo,
        titulo=payload.titulo,
        mensagem=payload.mensagem,
        valor=payload.valor,
        created_by=current_user.id,
    )
    db.add(aviso)
    db.flush()

    if payload.tipo == TipoAvisoDiretoEnum.MULTA:
        despesa = DespesaLancamento(
            predio_id=predio_id,
            unidade_id=payload.unidade_id,
            descricao=payload.titulo,
            categoria="multa",
            valor=payload.valor,
            data_vencimento=payload.data_vencimento,
            observacoes=payload.mensagem,
            status=StatusDespesaEnum.PENDENTE,
            created_by=current_user.id,
        )
        db.add(despesa)
        db.flush()
        aviso.despesa_lancamento_id = despesa.id
        db.add(aviso)
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

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="avisos_diretos",
        entidade_id=aviso.id,
        dados_depois=model_to_audit_dict(aviso),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(aviso)
    return aviso


@router.get("", response_model=list[AvisoDiretoRead])
def listar_avisos_diretos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
    unidade_id: int | None = None,
) -> list[AvisoDireto]:
    query = db.query(AvisoDireto).filter(AvisoDireto.deleted_at.is_(None))

    if current_user.roles_efetivos & set(_EMISSORES):
        if current_user.role == RoleEnum.ADMINISTRADOR:
            if predio_id is not None:
                query = query.filter(AvisoDireto.predio_id == predio_id)
        else:
            query = query.filter(AvisoDireto.predio_id == current_user.predio_id)
        if unidade_id is not None:
            query = query.filter(AvisoDireto.unidade_id == unidade_id)
    else:
        unidade_ids = [u.id for u in current_user.unidades]
        if not unidade_ids:
            return []
        papeis_destinatario = current_user.roles_efetivos & {
            RoleEnum.MORADOR,
            RoleEnum.PROPRIETARIO,
        }
        condicoes_destinatario = [AvisoDireto.destinatario == DestinatarioAvisoEnum.AMBOS] + [
            AvisoDireto.destinatario == DestinatarioAvisoEnum(papel.value)
            for papel in papeis_destinatario
        ]
        query = query.filter(
            AvisoDireto.predio_id == current_user.predio_id,
            AvisoDireto.unidade_id.in_(unidade_ids),
            or_(*condicoes_destinatario),
        )

    return query.order_by(AvisoDireto.created_at.desc()).all()


@router.get("/{aviso_id}", response_model=AvisoDiretoRead)
def obter_aviso_direto(
    aviso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> AvisoDireto:
    return _aviso_ou_404(db, aviso_id, current_user)


@router.post("/{aviso_id}/marcar-lido", response_model=AvisoDiretoRead)
def marcar_lido(
    aviso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> AvisoDireto:
    aviso = _aviso_ou_404(db, aviso_id, current_user)
    if aviso.lida_em is None:
        aviso.lida_em = datetime.now(timezone.utc)
        db.add(aviso)
        db.commit()
        db.refresh(aviso)
    return aviso


@router.post("/{aviso_id}/responder", response_model=AvisoDiretoRead)
def responder_aviso_direto(
    aviso_id: int,
    payload: AvisoDiretoResponder,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> AvisoDireto:
    aviso = _aviso_ou_404(db, aviso_id, current_user)
    if current_user.roles_efetivos & set(_EMISSORES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Só o destinatário do aviso pode respondê-lo.",
        )
    if aviso.resposta is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este aviso já foi respondido - resposta é única.",
        )

    dados_antes = model_to_audit_dict(aviso)
    agora = datetime.now(timezone.utc)
    aviso.resposta = payload.resposta
    aviso.respondido_por = current_user.id
    aviso.respondido_em = agora
    if aviso.lida_em is None:
        aviso.lida_em = agora
    db.add(aviso)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="avisos_diretos",
        entidade_id=aviso.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(aviso),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(aviso)
    return aviso


@router.delete("/{aviso_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_aviso_direto(
    aviso_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EMISSORES)),
) -> None:
    aviso = _aviso_ou_404(db, aviso_id, current_user)

    dados_antes = model_to_audit_dict(aviso)
    aviso.deleted_at = datetime.now(timezone.utc)
    db.add(aviso)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="SOFT_DELETE",
        entidade="avisos_diretos",
        entidade_id=aviso.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(aviso),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None
