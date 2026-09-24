from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.crypto import encrypt_secret
from app.core.dependencies import get_db, require_role
from app.core.security import hash_password
from app.core.viacep import (
    CepInvalidoError,
    CepNaoEncontradoError,
    CepServicoIndisponivelError,
    consultar_cep,
)
from app.models.enums import RoleEnum
from app.models.predio import Predio
from app.models.predio_convite import PredioConvite
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.schemas.predio import (
    CadastroViaConviteRequest,
    PredioConviteInfo,
    PredioConviteRead,
    PredioCreate,
    PredioIdentificarRequest,
    PredioIdentificarResponse,
    PredioIntegracaoOcrRequest,
    PredioIntegracaoOcrStatus,
    PredioModulosUpdate,
    PredioRead,
    UnidadeConviteInfo,
)
from app.schemas.usuario import UsuarioRead

router = APIRouter(tags=["predios"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _predio_ou_404(db: Session, predio_id: int) -> Predio:
    predio = db.get(Predio, predio_id)
    if predio is None or predio.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prédio não encontrado.")
    return predio


# ---------------------------------------------------------------------------
# Administração da plataforma (ADMINISTRADOR): cadastro de prédios e convites
# ---------------------------------------------------------------------------


@router.post("/predios", response_model=PredioRead, status_code=status.HTTP_201_CREATED)
def criar_predio(
    payload: PredioCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR)),
) -> Predio:
    try:
        endereco = consultar_cep(payload.cep)
    except CepInvalidoError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except CepNaoEncontradoError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CepServicoIndisponivelError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    ja_existe = (
        db.query(Predio)
        .filter(Predio.cep == payload.cep, Predio.numero == payload.numero)
        .first()
    )
    if ja_existe is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um prédio cadastrado com este CEP e número.",
        )

    predio = Predio(
        nome=payload.nome,
        cep=payload.cep,
        numero=payload.numero,
        complemento=payload.complemento,
        logradouro=endereco.logradouro,
        bairro=endereco.bairro,
        cidade=endereco.cidade,
        uf=endereco.uf,
        modulos_habilitados=[m.value for m in payload.modulos_habilitados],
        created_by=current_user.id,
    )
    db.add(predio)
    db.flush()

    for unidade_inicial in payload.unidades:
        db.add(
            Unidade(
                predio_id=predio.id,
                bloco=unidade_inicial.bloco,
                numero=unidade_inicial.numero,
                created_by=current_user.id,
            )
        )
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="predios",
        entidade_id=predio.id,
        dados_depois=model_to_audit_dict(predio),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(predio)
    return predio


@router.get("/predios", response_model=list[PredioRead])
def listar_predios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR)),
    incluir_inativos: bool = False,
) -> list[Predio]:
    query = db.query(Predio)
    if not incluir_inativos:
        query = query.filter(Predio.deleted_at.is_(None))
    return query.order_by(Predio.nome).all()


@router.get("/predios/{predio_id}", response_model=PredioRead)
def obter_predio(
    predio_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR)),
) -> Predio:
    return _predio_ou_404(db, predio_id)


@router.put("/predios/{predio_id}/modulos", response_model=PredioRead)
def atualizar_modulos(
    predio_id: int,
    payload: PredioModulosUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR)),
) -> Predio:
    """Habilita/desabilita módulos de um prédio - substitui a lista inteira
    (não incremental). Só o administrador da plataforma decide o que cada
    prédio contratou."""
    predio = _predio_ou_404(db, predio_id)

    predio.modulos_habilitados = [m.value for m in payload.modulos_habilitados]
    db.add(predio)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="predios",
        entidade_id=predio.id,
        dados_depois={"modulos_habilitados": predio.modulos_habilitados},
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(predio)
    return predio


@router.post("/predios/{predio_id}/convite", response_model=PredioConviteRead)
def gerar_convite(
    predio_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)),
) -> PredioConvite:
    """(Re)gera o link de autocadastro de um prédio. Síndico só pode gerar
    para o PRÓPRIO prédio; administrador (sem prédio) pode gerar para
    qualquer um. Reemitir desativa o convite anterior (um só ativo por vez -
    evita links antigos "esquecidos" continuarem funcionando)."""
    predio = _predio_ou_404(db, predio_id)
    if current_user.role != RoleEnum.ADMINISTRADOR and current_user.predio_id != predio.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode gerar convite para o próprio prédio.",
        )

    db.query(PredioConvite).filter(
        PredioConvite.predio_id == predio.id, PredioConvite.ativo.is_(True)
    ).update({"ativo": False})

    convite = PredioConvite(
        predio_id=predio.id,
        token=secrets.token_urlsafe(32),
        ativo=True,
        created_by=current_user.id,
    )
    db.add(convite)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="predio_convites",
        entidade_id=convite.id,
        dados_depois=model_to_audit_dict(convite),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(convite)
    return convite


@router.delete("/predios/{predio_id}/convite", status_code=status.HTTP_204_NO_CONTENT)
def revogar_convite(
    predio_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)),
) -> None:
    predio = _predio_ou_404(db, predio_id)
    if current_user.role != RoleEnum.ADMINISTRADOR and current_user.predio_id != predio.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode revogar o convite do próprio prédio.",
        )

    atualizados = (
        db.query(PredioConvite)
        .filter(PredioConvite.predio_id == predio.id, PredioConvite.ativo.is_(True))
        .update({"ativo": False})
    )
    if atualizados:
        registrar_log(
            db,
            usuario_id=current_user.id,
            acao="UPDATE",
            entidade="predio_convites",
            entidade_id=None,
            dados_depois={"predio_id": predio.id, "ativo": False},
            ip_origem=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    db.commit()
    return None


def _autorizar_gestor_do_predio(current_user: Usuario, predio: Predio) -> None:
    if current_user.role != RoleEnum.ADMINISTRADOR and current_user.predio_id != predio.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode gerenciar o próprio prédio.",
        )


@router.put("/predios/{predio_id}/integracao-ocr", response_model=PredioIntegracaoOcrStatus)
def configurar_integracao_ocr(
    predio_id: int,
    payload: PredioIntegracaoOcrRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)),
) -> PredioIntegracaoOcrStatus:
    """Configura a chave de API do Groq usada no OCR de boletos deste
    prédio - deve ser uma chave de uma conta do próprio condomínio (cada
    prédio usa/paga sua própria cota), nunca uma chave global do sistema.
    A chave nunca é registrada em texto plano (nem no banco, nem no log de
    auditoria - ver `_CAMPOS_SENSIVEIS` em app/core/audit.py)."""
    predio = _predio_ou_404(db, predio_id)
    _autorizar_gestor_do_predio(current_user, predio)

    predio.groq_api_key_cifrada = encrypt_secret(payload.groq_api_key)
    db.add(predio)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="predios",
        entidade_id=predio.id,
        dados_depois={"groq_api_key_configurada": True},
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return PredioIntegracaoOcrStatus(configurado=True)


@router.get("/predios/{predio_id}/integracao-ocr", response_model=PredioIntegracaoOcrStatus)
def obter_integracao_ocr(
    predio_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)),
) -> PredioIntegracaoOcrStatus:
    predio = _predio_ou_404(db, predio_id)
    _autorizar_gestor_do_predio(current_user, predio)
    return PredioIntegracaoOcrStatus(configurado=predio.groq_api_key_cifrada is not None)


@router.delete("/predios/{predio_id}/integracao-ocr", status_code=status.HTTP_204_NO_CONTENT)
def remover_integracao_ocr(
    predio_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)),
) -> None:
    predio = _predio_ou_404(db, predio_id)
    _autorizar_gestor_do_predio(current_user, predio)
    if predio.groq_api_key_cifrada is None:
        return None

    predio.groq_api_key_cifrada = None
    db.add(predio)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="predios",
        entidade_id=predio.id,
        dados_depois={"groq_api_key_configurada": False},
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Público (sem autenticação): identificar prédio no login + autocadastro
# ---------------------------------------------------------------------------


@router.post("/predios/identificar", response_model=PredioIdentificarResponse)
def identificar_predio(payload: PredioIdentificarRequest, db: Session = Depends(get_db)) -> Predio:
    """1a etapa do login (ver README/roadmap): o usuário informa CEP+número
    do prédio antes de e-mail/senha. Endpoint público de propósito - só
    devolve o nome/cidade/UF do prédio (nada sensível), o suficiente para a
    tela de login confirmar "é este o seu prédio?" antes do passo 2."""
    predio = (
        db.query(Predio)
        .filter(
            Predio.cep == payload.cep,
            Predio.numero == payload.numero,
            Predio.deleted_at.is_(None),
        )
        .first()
    )
    if predio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum prédio encontrado para este CEP e número.",
        )
    return predio


def _convite_valido_ou_404(db: Session, token: str) -> PredioConvite:
    convite = db.query(PredioConvite).filter(PredioConvite.token == token).first()
    if convite is None or not convite.esta_valido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convite inválido ou expirado.")
    return convite


@router.get("/predios/convite/{token}", response_model=PredioConviteInfo)
def obter_info_convite(token: str, db: Session = Depends(get_db)) -> PredioConviteInfo:
    """Público: a tela de autocadastro usa isto para mostrar o nome do
    prédio e a lista de unidades (para o morador escolher a(s) sua(s)) -
    nunca dados de outros usuários ou de outros prédios."""
    convite = _convite_valido_ou_404(db, token)
    unidades = (
        db.query(Unidade)
        .filter(Unidade.predio_id == convite.predio_id, Unidade.deleted_at.is_(None))
        .order_by(Unidade.bloco, Unidade.numero)
        .all()
    )
    return PredioConviteInfo(
        predio_nome=convite.predio.nome,
        predio_id=convite.predio_id,
        unidades=[UnidadeConviteInfo.model_validate(u) for u in unidades],
    )


@router.post(
    "/predios/convite/{token}/cadastro",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
)
def autocadastro_via_convite(
    token: str,
    payload: CadastroViaConviteRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Usuario:
    """Público: autocadastro de morador/proprietário via link do convite.
    Papéis de "equipe" (síndico/zelador/administrador) NUNCA passam por
    aqui - são criados por quem já tem acesso ao sistema (POST /usuarios)."""
    convite = _convite_valido_ou_404(db, token)

    ja_existe = (
        db.query(Usuario)
        .filter(Usuario.predio_id == convite.predio_id, Usuario.email == payload.email)
        .first()
    )
    if ja_existe is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um usuário com este e-mail neste prédio.",
        )

    unidades = (
        db.query(Unidade)
        .filter(
            Unidade.id.in_(payload.unidade_ids),
            Unidade.predio_id == convite.predio_id,
            Unidade.deleted_at.is_(None),
        )
        .all()
    )
    if len(unidades) != len(set(payload.unidade_ids)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uma ou mais unidades informadas não pertencem a este prédio.",
        )

    usuario = Usuario(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=RoleEnum(payload.role),
        predio_id=convite.predio_id,
        unidades=unidades,
    )
    db.add(usuario)
    db.flush()

    registrar_log(
        db,
        usuario_id=usuario.id,
        acao="CREATE",
        entidade="usuarios",
        entidade_id=usuario.id,
        dados_depois=model_to_audit_dict(usuario),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(usuario)
    return usuario
