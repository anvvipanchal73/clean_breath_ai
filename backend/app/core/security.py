"""
Field-level encryption for optional health data.
Uses Fernet (AES-128-CBC + HMAC-SHA256) from the cryptography package.

Health notes are ONLY stored with explicit user consent.
If HEALTH_DATA_ENCRYPTION_KEY is not set, any attempt to store health notes
raises a ValueError so the application fails loudly rather than storing
plaintext.
"""
from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet(key: str) -> Fernet:
    return Fernet(key.encode())


def encrypt_health_note(plaintext: str, key: str) -> bytes:
    """Encrypt a health note string.  Returns encrypted bytes."""
    if not key:
        raise ValueError("HEALTH_DATA_ENCRYPTION_KEY is not set; cannot store health data.")
    return _get_fernet(key).encrypt(plaintext.encode())


def decrypt_health_note(ciphertext: bytes, key: str) -> str:
    """Decrypt a health note.  Returns plaintext string."""
    if not key:
        raise ValueError("HEALTH_DATA_ENCRYPTION_KEY is not set; cannot decrypt health data.")
    try:
        return _get_fernet(key).decrypt(ciphertext).decode()
    except InvalidToken as exc:
        raise ValueError("Health data decryption failed – possible key mismatch.") from exc
