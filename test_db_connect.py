import asyncio
import sys
import os

# Add the current directory to sys.path to ensure we can import services
sys.path.append(os.getcwd())

try:
    from services.common.session_repository import PostgresSessionStore
    print("Successfully imported PostgresSessionStore")
except ImportError as e:
    print(f"Failed to import PostgresSessionStore: {e}")
    sys.exit(1)

async def test_connect():
    store = PostgresSessionStore()
    try:
        await store.ping()
        print("Successfully pinged Postgres")
    except Exception as e:
        print(f"Failed to ping Postgres: {e}")

if __name__ == "__main__":
    asyncio.run(test_connect())
