import asyncio
import logging

from services.common.profile_repository import ProfileStore

logging.basicConfig(level=logging.INFO)


async def main():
    import os

    dsn = os.getenv(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
    print(f"Connecting to {dsn}")
    store = ProfileStore(dsn=dsn)
    try:
        await store.ensure_schema()
        print(os.getenv(os.getenv("")))
        profiles = await store.list_active_profiles()
        print(f"Active profiles: {[p.name for p in profiles]}")
    finally:
        await store.close()


if __name__ == os.getenv(os.getenv("")):
    asyncio.run(main())
