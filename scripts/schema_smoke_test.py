"""Basic schema smoke tests for SomaAgent 01 events.

Run locally with:
    python scripts/schema_smoke_test.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_validator():
    module_path = Path("services/common/schema_validator.py").resolve()
    spec = importlib.util.spec_from_file_location("schema_validator", module_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def main() -> None:
    validator = _load_validator()

    validator.validate_event(
        {
            "event_id": "00000000-0000-0000-0000-000000000000",
            "session_id": "local-session",
            "role": "assistant",
            "message": "Hello from SomaAgent",
            "metadata": {"source": "smoke"},
        },
        "conversation_event",
    )

    validator.validate_event(
        {
            "event_id": "11111111-1111-1111-1111-111111111111",
            "session_id": "local-session",
            "tool_name": "echo",
            "status": "success",
            "payload": {"message": "pong"},
            "metadata": {"source": "smoke"},
            "execution_time": 0.1,
        },
        "tool_event",
    )

    print("Schema smoke test passed.")


if __name__ == "__main__":
    main()
