"""Criptografia simétrica reversível para segredos de terceiros que o
próprio sistema precisa reapresentar depois (ex.: a chave de API do Groq
que cada prédio configura para OCR de boletos).

Diferente de senha (Argon2, `app/core/security.py` — hash irreversível de
propósito), aqui o valor original precisa ser recuperado para autenticar
contra a API externa, então usamos criptografia simétrica (Fernet/AES) em
vez de hash.

A chave de criptografia é DERIVADA de `SECRET_KEY` (não é um segredo novo a
provisionar/rotacionar separadamente) com domain separation via SHA-256 —
mesma implicação prática de rotacionar `SECRET_KEY` hoje (invalida sessões
JWT): rotacionar `SECRET_KEY` também tornaria ilegíveis os segredos já
cifrados no banco. Aceitável nesta fase (mesma superfície de risco já
assumida para JWT).
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

__all__ = ["DecryptError", "decrypt_secret", "encrypt_secret"]


class DecryptError(RuntimeError):
    """O valor armazenado não pôde ser decifrado (corrompido, ou `SECRET_KEY`
    mudou desde que foi cifrado)."""


def _fernet() -> Fernet:
    settings = get_settings()
    digest = hashlib.sha256(f"meupredio-integracoes-terceiros:{settings.SECRET_KEY}".encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(valor: str) -> str:
    return _fernet().encrypt(valor.encode()).decode()


def decrypt_secret(valor_cifrado: str) -> str:
    try:
        return _fernet().decrypt(valor_cifrado.encode()).decode()
    except InvalidToken as exc:
        raise DecryptError("Nao foi possivel decifrar o segredo armazenado.") from exc
