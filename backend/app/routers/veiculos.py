from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_current_user, get_db, require_role
from app.models.enums import RoleEnum
from app.models.unidade import Unidade
from app.models.usuario import Usuario
from app.models.veiculo import Veiculo
from app.schemas.veiculo import VeiculoCreate, VeiculoRead, VeiculoUpdate

router = APIRouter(prefix="/veiculos", tags=["veiculos"])

# Papéis "operacionais": além da gestão, o zelador cadastra/consulta veículos
# no dia a dia da portaria.
_OPERACIONAIS = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO, RoleEnum.ZELADOR)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _veiculo_ou_404(db: Session, veiculo_id: int) -> Veiculo:
    veiculo = db.get(Veiculo, veiculo_id)
    if veiculo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")
    return veiculo


def _validar_unidade(db: Session, unidade_id: int, current_user: Usuario) -> Unidade:
    unidade = db.get(Unidade, unidade_id)
    if unidade is None or unidade.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")
    # Isolamento multi-tenant: um síndico/zelador não cadastra veículo em
    # unidade de outro prédio (administrador, sem prédio, fica de fora).
    if current_user.role != RoleEnum.ADMINISTRADOR and unidade.predio_id != current_user.predio_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidade não encontrada.")
    return unidade


def _autorizar_acesso_morador(current_user: Usuario, veiculo: Veiculo) -> None:
    """Um morador/proprietário só enxerga veículos das PRÓPRIAS unidades
    (relação N:N - pode ter mais de uma); papéis operacionais
    (administrador/síndico/zelador) enxergam qualquer veículo do prédio."""
    if current_user.role in _OPERACIONAIS:
        return
    minhas_unidades = {u.id for u in current_user.unidades}
    if veiculo.unidade_id not in minhas_unidades:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você só pode acessar veículos das suas próprias unidades.",
        )


@router.post("", response_model=VeiculoRead, status_code=status.HTTP_201_CREATED)
def criar_veiculo(
    payload: VeiculoCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_OPERACIONAIS)),
) -> Veiculo:
    _validar_unidade(db, payload.unidade_id, current_user)

    veiculo = Veiculo(
        unidade_id=payload.unidade_id,
        placa=payload.placa,
        modelo=payload.modelo,
        cor=payload.cor,
        tipo=payload.tipo,
        created_by=current_user.id,
    )
    db.add(veiculo)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="veiculos",
        entidade_id=veiculo.id,
        dados_depois=model_to_audit_dict(veiculo),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(veiculo)
    return veiculo


@router.get("", response_model=list[VeiculoRead])
def listar_veiculos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    unidade_id: int | None = None,
    incluir_inativos: bool = False,
) -> list[Veiculo]:
    query = db.query(Veiculo).join(Unidade, Veiculo.unidade_id == Unidade.id)
    if not incluir_inativos:
        query = query.filter(Veiculo.deleted_at.is_(None))

    if current_user.role in _OPERACIONAIS:
        if current_user.role != RoleEnum.ADMINISTRADOR:
            query = query.filter(Unidade.predio_id == current_user.predio_id)
        if unidade_id is not None:
            query = query.filter(Veiculo.unidade_id == unidade_id)
    else:
        # Morador/proprietário: sempre restrito às próprias unidades,
        # ignorando qualquer unidade_id que tente passar via query string.
        minhas_unidades = [u.id for u in current_user.unidades]
        if not minhas_unidades:
            return []
        query = query.filter(Veiculo.unidade_id.in_(minhas_unidades))

    return query.order_by(Veiculo.id).all()


@router.get("/{veiculo_id}", response_model=VeiculoRead)
def obter_veiculo(
    veiculo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Veiculo:
    veiculo = _veiculo_ou_404(db, veiculo_id)
    _autorizar_acesso_morador(current_user, veiculo)
    return veiculo


@router.patch("/{veiculo_id}", response_model=VeiculoRead)
def atualizar_veiculo(
    veiculo_id: int,
    payload: VeiculoUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_OPERACIONAIS)),
) -> Veiculo:
    veiculo = _veiculo_ou_404(db, veiculo_id)
    campos_enviados = payload.model_dump(exclude_unset=True)

    if "unidade_id" in campos_enviados:
        _validar_unidade(db, campos_enviados["unidade_id"], current_user)

    dados_antes = model_to_audit_dict(veiculo)

    for campo in ("unidade_id", "placa", "modelo", "cor", "tipo"):
        if campo in campos_enviados:
            setattr(veiculo, campo, campos_enviados[campo])

    db.add(veiculo)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="veiculos",
        entidade_id=veiculo.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(veiculo),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(veiculo)
    return veiculo


@router.delete("/{veiculo_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_veiculo(
    veiculo_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_OPERACIONAIS)),
) -> None:
    veiculo = _veiculo_ou_404(db, veiculo_id)
    if veiculo.deleted_at is not None:
        return None

    dados_antes = model_to_audit_dict(veiculo)
    veiculo.deleted_at = datetime.now(timezone.utc)
    db.add(veiculo)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="SOFT_DELETE",
        entidade="veiculos",
        entidade_id=veiculo.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(veiculo),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None
