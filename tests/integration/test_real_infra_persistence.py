import asyncio
import logging
import sys
import uuid

import pytest

from services.common.cognitive_state_repository import CognitiveStateStore
from src.core.config import cfg

# Configure logging to stdout
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


@pytest.mark.asyncio
async def test_real_infra_persistence():
    """Verify CognitiveStateStore against real PostgreSQL."""

    # 1. Setup
    # Ensure we are using the correct DSN for host-side access
    # cfg.settings().database.dsn should be correct if env vars are set,
    # or we might need to override host to localhost if it points to 'postgres' container name.

    dsn = cfg.settings().database.dsn
    print(f"Using DSN: {dsn}")

    # If running from host, 'postgres' hostname might not resolve.
    # Docker compose maps postgres:5432 to localhost:20002 (default)
    if "@postgres" in dsn:
        # Handle standard port or no port
        if ":5432" in dsn:
            dsn = dsn.replace("@postgres:5432", "@localhost:20002")
        else:
            dsn = dsn.replace("@postgres", "@localhost:20002")
        print(f"Adjusted DSN for host: {dsn}")

    store = CognitiveStateStore(dsn)

    # 2. Test Data
    session_id = f"test_session_{uuid.uuid4()}"
    state_data = {"dopamine": 0.75, "serotonin": 0.33, "norepinephrine": 0.1, "mood": "curious"}

    # 3. Save State
    print(f"Saving state for session {session_id}...")
    await store.save_state(session_id, state_data)

    # 4. Load State
    print(f"Loading state for session {session_id}...")
    loaded_state = await store.load_state(session_id)

    # 5. Verify
    assert loaded_state is not None
    assert loaded_state["dopamine"] == 0.75
    assert loaded_state["serotonin"] == 0.33
    assert loaded_state["mood"] == "curious"

    print("✅ Real infrastructure persistence verified!")

    # 6. Update State
    new_state = state_data.copy()
    new_state["dopamine"] = 0.99
    await store.save_state(session_id, new_state)

    updated_state = await store.load_state(session_id)
    assert updated_state["dopamine"] == 0.99
    print("✅ Update verified!")


if __name__ == "__main__":
    asyncio.run(test_real_infra_persistence())
