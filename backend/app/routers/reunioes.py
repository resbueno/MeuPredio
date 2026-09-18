from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_db, require_role, resolver_predio_id
from app.core.notificacoes import ids_usuarios_do_predio, notificar_usuarios
from app.models.enums import RoleEnum, StatusReuniaoEnum, TipoNotificacaoEnum
from app.models.reuniao import Reuniao
from app.models.reuniao_presenca import ReuniaoPresenca
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.reuniao import (
    PresencaCreate,
    PresencaRead,
    ReuniaoAtaInput,
    ReuniaoAtualizar,
    ReuniaoCreate,
    ReuniaoRead,
)

router = APIRouter(prefix="/reunioes", tags=["reunioes"])

# Quem convoca/edita/cancela/registra ata - decisao de sindico/administrador,
# nunca zelador (papel operacional, nao de governanca do condominio).
_GESTAO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _reuniao_ou_404(db: Session, reuniao_id: int, current_user: Usuario) -> Reuniao:
    reuniao = db.get(Reuniao, reuniao_id)
    if reuniao is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reunião não encontrada.")
    if current_user.role != RoleEnum.ADMINISTRADOR and reuniao.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reunião não encontrada.")
    return reuniao


def _exigir_convocada(reuniao: Reuniao, acao: str) -> None:
    if reuniao.status != StatusReuniaoEnum.CONVOCADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Só é possível {acao} uma reunião com status 'convocada' (status atual: {reuniao.status.value}).",
        )


@router.post("", response_model=ReuniaoRead, status_code=status.HTTP_201_CREATED)
def convocar_reuniao(
    payload: ReuniaoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> Reuniao:
    predio_id = resolver_predio_id(current_user, payload.predio_id)

    reuniao = Reuniao(
        predio_id=predio_id,
        tipo=payload.tipo,
        status=StatusReuniaoEnum.CONVOCADA,
        titulo=payload.titulo,
        data_hora=payload.data_hora,
        local=payload.local,
        pauta=payload.pauta,
        created_by=current_user.id,
    )
    db.add(reuniao)
    db.flush()

    destinatarios = ids_usuarios_do_predio(db, predio_id) - {current_user.id}
    notificar_usuarios(
        db,
        predio_id=predio_id,
        usuario_ids=destinatarios,
        tipo=TipoNotificacaoEnum.REUNIAO,
        titulo=f"Reunião convocada: {reuniao.titulo}",
        mensagem=f"{reuniao.local} - {reuniao.data_hora.strftime('%d/%m/%Y %H:%M')}",
        referencia_tipo="reuniao",
        referencia_id=reuniao.id,
    )

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="reunioes",
        entidade_id=reuniao.id,
        dados_depois=model_to_audit_dict(reuniao),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(reuniao)
    return reuniao


@router.get("", response_model=list[ReuniaoRead])
def listar_reunioes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
    predio_id: int | None = None,
    status_: StatusReuniaoEnum | None = None,
) -> list[Reuniao]:
    query = db.query(Reuniao)

    if current_user.role == RoleEnum.ADMINISTRADOR:
        if predio_id is not None:
            query = query.filter(Reuniao.predio_id == predio_id)
    else:
        query = query.filter(Reuniao.predio_id == current_user.predio_id)

    if status_ is not None:
        query = query.filter(Reuniao.status == status_)

    return query.order_by(Reuniao.data_hora.desc()).all()


@router.get("/{reuniao_id}", response_model=ReuniaoRead)
def obter_reuniao(
    reuniao_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> Reuniao:
    return _reuniao_ou_404(db, reuniao_id, current_user)


@router.patch("/{reuniao_id}", response_model=ReuniaoRead)
def atualizar_reuniao(
    reuniao_id: int,
    payload: ReuniaoAtualizar,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> Reuniao:
    reuniao = _reuniao_ou_404(db, reuniao_id, current_user)
    _exigir_convocada(reuniao, "editar")

    campos_enviados = payload.model_dump(exclude_unset=True)
    dados_antes = model_to_audit_dict(reuniao)
    for campo in ("tipo", "titulo", "data_hora", "local", "pauta"):
        if campo in campos_enviados:
            setattr(reuniao, campo, campos_enviados[campo])
    db.add(reuniao)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="reunioes",
        entidade_id=reuniao.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(reuniao),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(reuniao)
    return reuniao


@router.post("/{reuniao_id}/cancelar", response_model=ReuniaoRead)
def cancelar_reuniao(
    reuniao_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> Reuniao:
    reuniao = _reuniao_ou_404(db, reuniao_id, current_user)
    _exigir_convocada(reuniao, "cancelar")

    dados_antes = model_to_audit_dict(reuniao)
    reuniao.status = StatusReuniaoEnum.CANCELADA
    db.add(reuniao)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="reunioes",
        entidade_id=reuniao.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(reuniao),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(reuniao)
    return reuniao


@router.post("/{reuniao_id}/ata", response_model=ReuniaoRead)
def registrar_ata(
    reuniao_id: int,
    payload: ReuniaoAtaInput,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> Reuniao:
    """Registra a ata e fecha o ciclo da reunião (vira 'realizada') - a
    partir daí não é mais possível editar convocação/pauta nem confirmar
    presença, só o essencial de uma reunião que já aconteceu."""
    reuniao = _reuniao_ou_404(db, reuniao_id, current_user)
    _exigir_convocada(reuniao, "registrar a ata de")

    dados_antes = model_to_audit_dict(reuniao)
    reuniao.ata = payload.ata
    reuniao.ata_registrada_em = datetime.now(timezone.utc)
    reuniao.ata_registrada_por = current_user.id
    reuniao.status = StatusReuniaoEnum.REALIZADA
    db.add(reuniao)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="reunioes",
        entidade_id=reuniao.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(reuniao),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(reuniao)
    return reuniao


@router.post(
    "/{reuniao_id}/presenca", response_model=PresencaRead, status_code=status.HTTP_201_CREATED
)
def confirmar_presenca(
    reuniao_id: int,
    payload: PresencaCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role()),
) -> ReuniaoPresenca:
    reuniao = _reuniao_ou_404(db, reuniao_id, current_user)
    _exigir_convocada(reuniao, "confirmar presença em")

    e_gestao = bool(current_user.roles_efetivos & set(_GESTAO))
    if not e_gestao and payload.unidade_id not in {u.id for u in current_user.unidades}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode confirmar presença pela própria unidade.",
        )

    unidade = db.get(Unidade, payload.unidade_id)
    if unidade is None or unidade.deleted_at is not None or unidade.predio_id != reuniao.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")

    presenca = ReuniaoPresenca(
        reuniao_id=reuniao.id,
        unidade_id=payload.unidade_id,
        created_by=current_user.id,
    )
    db.add(presenca)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta unidade já confirmou presença nesta reunião.",
        ) from None

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="reunioes_presencas",
        entidade_id=presenca.id,
        dados_depois=model_to_audit_dict(presenca),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(presenca)
    return presenca


@router.delete("/{reuniao_id}/presenca/{unidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_presenca(
    reuniao_id: int,
    unidade_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_GESTAO)),
) -> None:
    reuniao = _reuniao_ou_404(db, reuniao_id, current_user)
    _exigir_convocada(reuniao, "alterar presença de")

    presenca = (
        db.query(ReuniaoPresenca)
        .filter(ReuniaoPresenca.reuniao_id == reuniao.id, ReuniaoPresenca.unidade_id == unidade_id)
        .one_or_none()
    )
    if presenca is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Presença não encontrada.")

    dados_antes = model_to_audit_dict(presenca)
    db.delete(presenca)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="DELETE",
        entidade="reunioes_presencas",
        entidade_id=presenca.id,
        dados_antes=dados_antes,
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None
