"""Hashing de senha (Argon2) e emissão/validação de JWT.

Nenhum segredo fica hardcoded aqui: SECRET_KEY vem de `Settings`
(`app/core/config.py`), que por sua vez lê apenas de variáveis de ambiente.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# Argon2id é o algoritmo recomendado atualmente (OWASP) para hashing de senha:
# resistente tanto a ataques por GPU quanto a ataques com hardware dedicado.
_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(*, subject: str, role: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Gera um JWT assinado (HS256 por padrão) com a role embutida no payload.

    `subject` deve ser o id do usuário (como string) — usado por
    `get_current_user` para carregar o usuário do banco a cada request.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica e valida assinatura + expiração do JWT.

    Levanta `jose.exceptions.JWTError` (ou subclasses, como `ExpiredSignatureError`)
    se o token for inválido, expirado ou adulterado. O algoritmo é fixado
    explicitamente em `[settings.JWT_ALGORITHM]` para não aceitar um token
    assinado com um algoritmo diferente do esperado (ex.: ataque "alg=none").
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
