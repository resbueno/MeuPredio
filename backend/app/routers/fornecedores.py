from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.audit import model_to_audit_dict, registrar_log
from app.core.dependencies import get_db, require_role
from app.models.enums import RoleEnum
from app.models.fornecedor import Fornecedor
from app.models.usuario import Usuario
from app.schemas.fornecedor import FornecedorCreate, FornecedorRead, FornecedorUpdate

router = APIRouter(prefix="/fornecedores", tags=["fornecedores"])

# Motor Financeiro (Fase 2): por ora restrito a síndico/administrador, os
# mesmos papéis que hoje respondem pela prestação de contas do condomínio.
# Moradores ganham acesso de leitura quando o Portal da Transparência
# (Fase 3) for implementado.
_FINANCEIRO = (RoleEnum.ADMINISTRADOR, RoleEnum.SINDICO)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _fornecedor_ou_404(db: Session, fornecedor_id: int) -> Fornecedor:
    fornecedor = db.get(Fornecedor, fornecedor_id)
    if fornecedor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fornecedor nao encontrado.")
    return fornecedor


def _validar_documento_unico(db: Session, documento: str | None, *, ignorar_id: int | None = None) -> None:
    if documento is None:
        return
    query = db.query(Fornecedor).filter(Fornecedor.documento == documento)
    if ignorar_id is not None:
        query = query.filter(Fornecedor.id != ignorar_id)
    if query.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ja existe um fornecedor cadastrado com este documento.",
        )


@router.post("", response_model=FornecedorRead, status_code=status.HTTP_201_CREATED)
def criar_fornecedor(
    payload: FornecedorCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> Fornecedor:
    _validar_documento_unico(db, payload.documento)

    fornecedor = Fornecedor(
        nome=payload.nome,
        documento=payload.documento,
        categoria=payload.categoria,
        telefone=payload.telefone,
        email=payload.email,
        observacoes=payload.observacoes,
        created_by=current_user.id,
    )
    db.add(fornecedor)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="CREATE",
        entidade="fornecedores",
        entidade_id=fornecedor.id,
        dados_depois=model_to_audit_dict(fornecedor),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


@router.get("", response_model=list[FornecedorRead])
def listar_fornecedores(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
    categoria: str | None = None,
    incluir_inativos: bool = False,
) -> list[Fornecedor]:
    query = db.query(Fornecedor)
    if not incluir_inativos:
        query = query.filter(Fornecedor.deleted_at.is_(None))
    if categoria is not None:
        query = query.filter(Fornecedor.categoria == categoria)
    return query.order_by(Fornecedor.nome).all()


@router.get("/{fornecedor_id}", response_model=FornecedorRead)
def obter_fornecedor(
    fornecedor_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> Fornecedor:
    return _fornecedor_ou_404(db, fornecedor_id)


@router.patch("/{fornecedor_id}", response_model=FornecedorRead)
def atualizar_fornecedor(
    fornecedor_id: int,
    payload: FornecedorUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> Fornecedor:
    fornecedor = _fornecedor_ou_404(db, fornecedor_id)
    campos_enviados = payload.model_dump(exclude_unset=True)

    if "documento" in campos_enviados:
        _validar_documento_unico(db, campos_enviados["documento"], ignorar_id=fornecedor.id)

    dados_antes = model_to_audit_dict(fornecedor)

    for campo in ("nome", "documento", "categoria", "telefone", "email", "observacoes"):
        if campo in campos_enviados:
            setattr(fornecedor, campo, campos_enviados[campo])

    db.add(fornecedor)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="UPDATE",
        entidade="fornecedores",
        entidade_id=fornecedor.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(fornecedor),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


@router.delete("/{fornecedor_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_fornecedor(
    fornecedor_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_role(*_FINANCEIRO)),
) -> None:
    fornecedor = _fornecedor_ou_404(db, fornecedor_id)
    if fornecedor.deleted_at is not None:
        return None

    dados_antes = model_to_audit_dict(fornecedor)
    fornecedor.deleted_at = datetime.now(timezone.utc)
    db.add(fornecedor)
    db.flush()

    registrar_log(
        db,
        usuario_id=current_user.id,
        acao="SOFT_DELETE",
        entidade="fornecedores",
        entidade_id=fornecedor.id,
        dados_antes=dados_antes,
        dados_depois=model_to_audit_dict(fornecedor),
        ip_origem=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()
    return None
