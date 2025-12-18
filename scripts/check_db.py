
import asyncio
import os
import sys
import asyncpg

# Add project root to path
sys.path.append(os.getcwd())

from src.core.config import cfg

async def check_db():
    try:
        print("Attempting DB connection...")
        # Use localhost mapped port for external access
        dsn = "postgresql://soma:soma@localhost:20002/somaagent01"
        print(f"Using Test DSN: {dsn}") 
        
        conn = await asyncpg.connect(dsn)
        try:
            result = await conn.fetchval("SELECT 1")
            print(f"DB Connection Successful: {result}")
        finally:
            await conn.close()
            
        print("SUCCESS")
    except Exception as e:
        print(f"FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(check_db())
