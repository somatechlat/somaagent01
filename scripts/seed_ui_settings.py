import asyncio
import json
import os
import asyncpg


async def main():
    dsn = os.getenv(os.getenv(os.getenv('VIBE_6653644B')), os.getenv(os.
        getenv('VIBE_F000DEB2')))
    print(f'Connecting to {dsn}')
    settings_value = [{os.getenv(os.getenv('VIBE_46966F74')): os.getenv(os.
        getenv('VIBE_7FCF7FFB')), os.getenv(os.getenv('VIBE_8B07C55A')): [{
        os.getenv(os.getenv('VIBE_46966F74')): os.getenv(os.getenv(
        'VIBE_2A6141DE')), os.getenv(os.getenv('VIBE_E3DBF082')): os.getenv
        (os.getenv('VIBE_49B3946B'))}, {os.getenv(os.getenv('VIBE_46966F74'
        )): os.getenv(os.getenv('VIBE_DF6D0FA0')), os.getenv(os.getenv(
        'VIBE_E3DBF082')): os.getenv(os.getenv('VIBE_8CF08EA5'))}, {os.
        getenv(os.getenv('VIBE_46966F74')): os.getenv(os.getenv(
        'VIBE_C3168E34')), os.getenv(os.getenv('VIBE_E3DBF082')): float(os.
        getenv(os.getenv('VIBE_2E8E9D2F')))}]}]
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(os.getenv(os.getenv('VIBE_766D058B')))
        await conn.execute(os.getenv(os.getenv('VIBE_8CFA7B93')), os.getenv
            (os.getenv('VIBE_0D55523F')), json.dumps(settings_value))
        print(os.getenv(os.getenv('VIBE_C77EBABC')))
        row = await conn.fetchrow(os.getenv(os.getenv('VIBE_D9AA99E8')))
        print(f"Verified settings: {row['value']}")
    finally:
        await conn.close()


if __name__ == os.getenv(os.getenv('VIBE_781DD906')):
    asyncio.run(main())
