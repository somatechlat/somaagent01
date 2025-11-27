import asyncio
import json
import os

import asyncpg


async def main():
    dsn = os.getenv(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
    print(f"Connecting to {dsn}")
    settings_value = [
        {
            os.getenv(os.getenv("")): os.getenv(os.getenv("")),
            os.getenv(os.getenv("")): [
                {
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                },
                {
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                },
                {
                    os.getenv(os.getenv("")): os.getenv(os.getenv("")),
                    os.getenv(os.getenv("")): float(os.getenv(os.getenv(""))),
                },
            ],
        }
    ]
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(os.getenv(os.getenv("")))
        await conn.execute(
            os.getenv(os.getenv("")), os.getenv(os.getenv("")), json.dumps(settings_value)
        )
        print(os.getenv(os.getenv("")))
        row = await conn.fetchrow(os.getenv(os.getenv("")))
        print(f"Verified settings: {row['value']}")
    finally:
        await conn.close()


if __name__ == os.getenv(os.getenv("")):
    asyncio.run(main())
