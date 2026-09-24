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


# Lista pequena e deliberada de senhas triviais que passariam na regra
# "mistura letra e número" mas são as primeiras que qualquer dicionário de
# força bruta tenta - normalizada para minúsculas na comparação, então cobre
# variações de maiúscula/minúscula (ex.: "Senha123" também cai aqui).
_SENHAS_COMUNS = {
    "senha123", "senha1234", "12345678", "123456789", "1234567890",
    "password", "password1", "password123", "qwerty123", "abc12345",
    "admin123", "condominio1", "predio123", "sindico123", "portaria123",
}


def validar_senha_forte(password: str) -> str | None:
    """Retorna a mensagem de erro se a senha for fraca, ou `None` se ok.
    Usado pelos 3 pontos onde uma senha nova é definida (cadastro de
    usuário, atualização e autocadastro via convite) - mantém a regra em
    um único lugar em vez de repetida em cada schema."""
    if password.isdigit() or password.isalpha():
        return "A senha deve ter ao menos 8 caracteres combinando letras e números."
    if password.lower() in _SENHAS_COMUNS:
        return "Essa senha é comum demais e fácil de adivinhar - escolha outra."
    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


# Hash "morto" (sem senha real correspondente) usado apenas para equalizar o
# tempo de resposta do login quando o e-mail informado não existe. Sem isso,
# um atacante poderia medir o tempo de resposta para distinguir "e-mail não
# cadastrado" (retorno imediato) de "e-mail cadastrado, senha errada"
# (retorno após o custo computacional do Argon2) — um side-channel clássico
# de user enumeration.
_DUMMY_HASH = _pwd_context.hash("senha-que-nunca-existe-usada-so-para-equalizar-tempo-de-resposta")


def verify_password_constant_time(plain_password: str, hashed_password: str | None) -> bool:
    """Como `verify_password`, mas tolera `hashed_password=None` (usuário
    inexistente): nesse caso verifica contra `_DUMMY_HASH` mesmo assim, para
    que o custo computacional (e portanto o tempo de resposta) seja o mesmo
    independente de o e-mail existir ou não. Sempre retorna False quando
    `hashed_password` é None."""
    is_real_user = hashed_password is not None
    result = _pwd_context.verify(plain_password, hashed_password or _DUMMY_HASH)
    return result and is_real_user


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
