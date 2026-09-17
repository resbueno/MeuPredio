from __future__ import annotations

import pytest

from app.core.crypto import DecryptError, decrypt_secret, encrypt_secret


def test_encrypt_then_decrypt_roundtrips():
    original = "chave-secreta-da-conta-do-condominio-123"
    cifrado = encrypt_secret(original)
    assert cifrado != original
    assert decrypt_secret(cifrado) == original


def test_valor_cifrado_nao_e_legivel_a_olho_nu():
    cifrado = encrypt_secret("gsk_exemplo-de-chave-groq")
    assert "gsk_exemplo" not in cifrado


def test_decrypt_de_valor_invalido_levanta_decrypt_error():
    with pytest.raises(DecryptError):
        decrypt_secret("isto-nao-e-um-token-fernet-valido")
