"""Module rfc_exchange."""

from admin.core.helpers import crypto, dotenv, runtime


async def get_root_password():
    """Retrieve root password."""

    if runtime.is_dockerized():
        pswd = _get_root_password()
    else:
        priv = crypto._generate_private_key()
        pub = crypto._generate_public_key(priv)
        enc = await runtime.call_development_function(_provide_root_password, pub)
        pswd = crypto.decrypt_data(enc, priv)
    return pswd


def _provide_root_password(public_key_pem: str):
    """Execute provide root password.

    Args:
        public_key_pem: The public_key_pem.
    """

    pswd = _get_root_password()
    enc = crypto.encrypt_data(pswd, public_key_pem)
    return enc


def _get_root_password():
    """Execute get root password."""

    return dotenv.get_dotenv_value(dotenv.KEY_ROOT_PASSWORD) or ""
