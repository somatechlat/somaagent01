import asyncio
import json
import os

import asyncpg


async def main():
    dsn = os.getenv("SA01_DB_DSN", "postgresql://soma:soma@localhost:20002/somaagent01")
    print(f"Connecting to {dsn}")

    settings_value = [
        {
            "id": "llm_settings",
            "fields": [
                {"id": "llm_model", "value": "llama3-8b-8192"},
                {"id": "llm_base_url", "value": "https://api.groq.com/openai/v1"},
                {"id": "llm_temperature", "value": 0.7},
            ],
        }
    ]

    conn = await asyncpg.connect(dsn)
    try:
        # Ensure table exists (it should, but just in case)
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ui_settings (
                key TEXT PRIMARY KEY,
                value JSONB
            );
        """
        )

        # Insert or update settings
        await conn.execute(
            """
            INSERT INTO ui_settings (key, value)
            VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE SET value = $2
        """,
            "sections",
            json.dumps(settings_value),
        )

        print("UI settings seeded successfully.")

        # Verify
        row = await conn.fetchrow("SELECT value FROM ui_settings WHERE key='sections'")
        print(f"Verified settings: {row['value']}")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
