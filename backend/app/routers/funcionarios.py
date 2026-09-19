from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_db, require_role
from app.models.enums import RoleEnum
from app.models.funcionario import Funcionario
from app.models.usuario import Usuario
from app.schemas.funcionario import FuncionarioAtualizar, FuncionarioCreate, FuncionarioRead

router = APIRouter(prefix="/funcionarios", tags=["funcionarios"])

# Só síndico e zelador criam e enxergam (contém salário e CPF) - nem o
# administrador global entra aqui, por decisão explícita do produto.
_EQUIPE = (RoleEnum.SINDICO, RoleEnum.ZELADOR)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _funcionario_ou_404(db: Session, funcionario_id: int, current_user: Usuario) -> Funcionario:
    funcionario = db.get(Funcionario, funcionario_id)
    if (
        funcionario is None
        or funcionario.deleted_at is not None
        or funcionario.predio_id != current_user.predio_id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Funcionário não encontrado.")
    return funcionario


@router.post("", response_model=FuncionarioRead, status_code=status.HTTP_201_CREATED)
def criar_funcionario(
    payload: FuncionarioCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EQUIPE)),
) -> Funcionario:
    funcionario = Funcionario(
        predio_id=current_user.predio_id,
        created_by=current_user.id,
        **payload.model_dump(),
    )
    db.add(funcionario)
    db.flush()
    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="funcionarios",
        entidade_id=funcionario.id,
        dados_depois=model_to_audit_dict(funcionario),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(funcionario)
    return funcionario


@router.get("", response_model=list[FuncionarioRead])
def listar_funcionarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EQUIPE)),
    incluir_inativos: bool = False,
) -> list[Funcionario]:
    query = db.query(Funcionario).filter(
        Funcionario.predio_id == current_user.predio_id, Funcionario.deleted_at.is_(None)
    )
    if not incluir_inativos:
        query = query.filter(Funcionario.ativo.is_(True))
    return query.order_by(Funcionario.nome_completo.asc()).all()


@router.patch("/{funcionario_id}", response_model=FuncionarioRead)
def atualizar_funcionario(
    funcionario_id: int,
    payload: FuncionarioAtualizar,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EQUIPE)),
) -> Funcionario:
    funcionario = _funcionario_ou_404(db, funcionario_id, current_user)
    dados_antes = model_to_audit_dict(funcionario)
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(funcionario, campo, valor)
    db.add(funcionario)
    db.flush()
    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="funcionarios",
        entidade_id=funcionario.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(funcionario),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(funcionario)
    return funcionario


@router.delete("/{funcionario_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_funcionario(
    funcionario_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_EQUIPE)),
) -> None:
    funcionario = _funcionario_ou_404(db, funcionario_id, current_user)
    dados_antes = model_to_audit_dict(funcionario)
    funcionario.deleted_at = datetime.now(timezone.utc)
    db.add(funcionario)
    db.flush()
    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="SOFT_DELETE",
        entidade="funcionarios",
        entidade_id=funcionario.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(funcionario),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None
