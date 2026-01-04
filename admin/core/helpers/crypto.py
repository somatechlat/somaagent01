"""Module crypto."""

import hashlib
import hmac

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def hash_data(data: str, password: str):
    """Execute hash data.

        Args:
            data: The data.
            password: The password.
        """

    return hmac.new(password.encode(), data.encode(), hashlib.sha256).hexdigest()


def verify_data(data: str, hash: str, password: str):
    """Execute verify data.

        Args:
            data: The data.
            hash: The hash.
            password: The password.
        """

    return hash_data(data, password) == hash


def _generate_private_key():
    """Execute generate private key.
        """

    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )


def _generate_public_key(private_key: rsa.RSAPrivateKey):
    """Execute generate public key.

        Args:
            private_key: The private_key.
        """

    return (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .hex()
    )


def _decode_public_key(public_key: str) -> rsa.RSAPublicKey:
    # Decode hex string back to bytes
    """Execute decode public key.

        Args:
            public_key: The public_key.
        """

    pem_bytes = bytes.fromhex(public_key)
    # Load the PEM public key
    key = serialization.load_pem_public_key(pem_bytes)
    if not isinstance(key, rsa.RSAPublicKey):
        raise TypeError("The provided key is not an RSAPublicKey")
    return key


def encrypt_data(data: str, public_key_pem: str):
    """Execute encrypt data.

        Args:
            data: The data.
            public_key_pem: The public_key_pem.
        """

    return _encrypt_data(data.encode("utf-8"), _decode_public_key(public_key_pem))


def _encrypt_data(data: bytes, public_key: rsa.RSAPublicKey):
    """Execute encrypt data.

        Args:
            data: The data.
            public_key: The public_key.
        """

    b = public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return b.hex()


def decrypt_data(data: str, private_key: rsa.RSAPrivateKey):
    """Execute decrypt data.

        Args:
            data: The data.
            private_key: The private_key.
        """

    b = private_key.decrypt(
        bytes.fromhex(data),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return b.decode("utf-8")