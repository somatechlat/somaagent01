#!/usr/bin/env python3
"""S3 – Rotate encryption key and re-encrypt all settings."""

import asyncio
import os

from python.helpers.vault_adapter import VaultAdapter
from services.common import env
from services.common.secret_manager import (
    get_internal_token,
    get_provider_key,
    list_providers,
    SecretManager,
    set_internal_token,
    set_provider_key,
)


def main():
    old_key = env.get("SA01_CRYPTO_FERNET_KEY")
    new_key = VaultAdapter.rotate_key()
    print(f"🔑 New key generated: {new_key}")
    # If an old key existed we need to re‑encrypt all stored secrets with the
    # newly generated key.  The secret manager automatically encrypts using the
    # current ``SA01_CRYPTO_FERNET_KEY`` environment variable, so we simply read
    # each secret and write it back – the write will use the new key.
    if old_key:

        async def _re_encrypt():
            sm = SecretManager()
            # Re‑encrypt provider keys
            for provider in await list_providers():
                key = await get_provider_key(provider)
                if key is not None:
                    await set_provider_key(provider, key)
            # Re‑encrypt internal token if present
            token = await get_internal_token()
            if token is not None:
                await set_internal_token(token)

        asyncio.run(_re_encrypt())
        print("🔄 All secrets re‑encrypted with the new key.")
    os.environ["SA01_CRYPTO_FERNET_KEY"] = new_key
    env.refresh()


if __name__ == "__main__":
    main()
