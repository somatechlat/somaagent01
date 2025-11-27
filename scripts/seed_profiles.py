import asyncio
import logging
from services.common.profile_repository import ProfileStore
logging.basicConfig(level=logging.INFO)


async def main():
    import os
    dsn = os.getenv(os.getenv(os.getenv('VIBE_8B567757')), os.getenv(os.
        getenv('VIBE_3C6E040E')))
    print(f'Connecting to {dsn}')
    store = ProfileStore(dsn=dsn)
    try:
        await store.ensure_schema()
        print(os.getenv(os.getenv('VIBE_D7C32A01')))
        profiles = await store.list_active_profiles()
        print(f'Active profiles: {[p.name for p in profiles]}')
    finally:
        await store.close()


if __name__ == os.getenv(os.getenv('VIBE_2265AE13')):
    asyncio.run(main())
