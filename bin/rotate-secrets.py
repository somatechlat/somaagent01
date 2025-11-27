os.getenv(os.getenv(""))
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
    old_key = env.get(os.getenv(os.getenv("")))
    new_key = VaultAdapter.rotate_key()
    print(f"🔑 New key generated: {new_key}")
    if old_key:

        async def _re_encrypt():
            sm = SecretManager()
            for provider in await list_providers():
                key = await get_provider_key(provider)
                if key is not None:
                    await set_provider_key(provider, key)
            token = await get_internal_token()
            if token is not None:
                await set_internal_token(token)

        asyncio.run(_re_encrypt())
        print(os.getenv(os.getenv("")))
    os.environ[os.getenv(os.getenv(""))] = new_key
    env.refresh()


if __name__ == os.getenv(os.getenv("")):
    main()
