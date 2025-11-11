"""M3: Central secrets adapter for settings encryption & rotation"""
import os
import base64
from cryptography.fernet import Fernet

class VaultAdapter:
    """Encrypt/decrypt provider keys and all runtime settings."""
    _cipher: Fernet | None = None

    @classmethod
    def cipher(cls) -> Fernet:
        if cls._cipher is None:
            key = os.getenv("SA01_CRYPTO_FERNET_KEY") or Fernet.generate_key()
            cls._cipher = Fernet(key.encode() if isinstance(key, str) else key)
        return cls._cipher

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        return cls.cipher().encrypt(plaintext.encode()).decode()

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        return cls.cipher().decrypt(ciphertext.encode()).decode()

    @classmethod
    def rotate_key(cls) -> str:
        """CLI helper: returns new base64 Fernet key."""
        new_key = Fernet.generate_key()
        return base64.urlsafe_b64encode(new_key).decode()
