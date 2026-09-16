from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.audit import registrar_log
from app.core.dependencies import get_db
from app.core.security import create_access_token, verify_password_constant_time
from app.models.usuario import Usuario
from app.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    usuario_elegivel = user is not None and not user.is_deleted

    # Executa a verificação de senha (com seu custo computacional Argon2)
    # SEMPRE, mesmo quando o e-mail não existe — contra um hash "morto" nesse
    # caso — para que o tempo de resposta não revele se o e-mail está
    # cadastrado (mitigação de user enumeration por timing side-channel).
    senha_confere = verify_password_constant_time(
        form_data.password,
        user.hashed_password if usuario_elegivel else None,
    )

    # Mensagem de erro genérica de propósito: não revela se o problema foi o
    # e-mail não encontrado ou a senha incorreta (evita "user enumeration").
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="E-mail ou senha invalidos.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not usuario_elegivel or not senha_confere:
        raise invalid_credentials
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inativo. Contate o administrador do condominio.",
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)

    token = create_access_token(subject=str(user.id), role=user.role.value)

    registrar_log(
        db,
        usuario_id=user.id,
        acao="LOGIN",
        entidade="usuarios",
        entidade_id=user.id,
        ip_origem=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.commit()

    return Token(access_token=token, token_type="bearer")
