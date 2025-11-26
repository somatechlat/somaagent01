import asyncio
import logging
import sys
from services.common.profile_repository import ProfileStore
from src.core.config import cfg

logging.basicConfig(level=logging.INFO)

async def main():
    import os
    dsn = os.getenv("SA01_DB_DSN", "postgresql://soma:soma@localhost:20002/somaagent01")
    print(f"Connecting to {dsn}")
    store = ProfileStore(dsn=dsn)
    try:
        await store.ensure_schema()
        print("Schema ensured and seeded.")
        
        profiles = await store.list_active_profiles()
        print(f"Active profiles: {[p.name for p in profiles]}")
    finally:
        await store.close()

if __name__ == "__main__":
    asyncio.run(main())
