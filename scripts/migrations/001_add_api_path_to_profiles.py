#!/usr/bin/env python3
"""One-off migration to add the api_path column to model_profiles."""

import asyncio
import os

import asyncpg


async def main():
    dsn = os.path.expandvars(os.getenv("POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"))
    conn = await asyncpg.connect(dsn)
    try:
        # Check if the column already exists
        column_exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'model_profiles' AND column_name = 'api_path'
            );
            """
        )

        if column_exists:
            print("Column 'api_path' already exists in 'model_profiles'. Migration not needed.")
            return

        print("Adding 'api_path' column to 'model_profiles' table...")
        await conn.execute("ALTER TABLE model_profiles ADD COLUMN api_path TEXT;")
        print("Migration successful.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
