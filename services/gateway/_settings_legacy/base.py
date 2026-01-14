"""M3: Central secrets adapter for settings encryption & rotation"""

import base64
import os

from cryptography.fernet import Fernet


def get_required_env(key: str, description: str) -> str:
    """Get required environment variable or raise error."""
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Required environment variable {key} ({description}) is not set")
    return value


class VaultAdapter:
    """Encrypt/decrypt provider keys and all runtime settings."""

    _cipher: Fernet | None = None

    @classmethod
    def cipher(cls) -> Fernet:
        """Execute cipher. Fails closed if key is missing to prevent data loss."""

        if cls._cipher is None:
            # Force explicit configuration. No runtime generation allowed.
            key = get_required_env("SA01_CRYPTO_FERNET_KEY", "Fernet encryption key")
            material = key.encode()
            cls._cipher = Fernet(material)
        return cls._cipher

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """Execute encrypt.

        Args:
            plaintext: The plaintext.
        """

        return cls.cipher().encrypt(plaintext.encode()).decode()

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """Execute decrypt.

        Args:
            ciphertext: The ciphertext.
        """

        return cls.cipher().decrypt(ciphertext.encode()).decode()

    @classmethod
    def rotate_key(cls) -> str:
        """CLI helper: returns new base64 Fernet key."""
        new_key = Fernet.generate_key()
        return base64.urlsafe_b64encode(new_key).decode()
