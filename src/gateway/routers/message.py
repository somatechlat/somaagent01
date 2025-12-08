"""Router that re‑exports message‑related endpoints.

The implementation lives in ``services.gateway.main`` where the endpoints are
attached directly to the FastAPI app. This module exposes wrappers that call
the existing functions, providing a clean module that can be mounted by
``services/gateway/service.py``.
"""

from fastapi import APIRouter

# Import the original endpoint callables. They are defined as regular async
# functions with FastAPI dependency injection – importing them preserves the
# signatures and injected dependencies.
from services.gateway.main import (
    enqueue_message,
    enqueue_quick_action,
    upload_files,
)

router = APIRouter()

# Re‑register the three routes under the same paths. The ``endpoint`` argument
# is used to attach the existing function without creating a new wrapper.
router.add_api_route(
    "/v1/session/message",
    endpoint=enqueue_message,
    methods=["POST"],
    include_in_schema=False,
)

router.add_api_route(
    "/v1/uploads",
    endpoint=upload_files,
    methods=["POST"],
    include_in_schema=False,
)

router.add_api_route(
    "/v1/session/action",
    endpoint=enqueue_quick_action,
    methods=["POST"],
    include_in_schema=False,
)
