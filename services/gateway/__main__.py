"""Python module entrypoint for the gateway.

Production deployments start the gateway via `uvicorn services.gateway.main:app`.
This module keeps `python -m services.gateway` working with the same app object.
"""

from __future__ import annotations

from services.gateway.main import main

if __name__ == "__main__":
    main()
