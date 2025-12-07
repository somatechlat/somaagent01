"""Weights router exposing the Somabrain learning weights endpoint.

The original monolith provided a ``/v1/weights`` endpoint used by the client
side and the test suite. During the refactor the route was unintentionally
omitted, causing OpenAPI validation failures. This router reinstates the
endpoint in a minimal, production‑ready fashion by delegating to the shared
``services.common.learning.get_weights`` helper, which already contains the
logic for contacting SomaBrain (or a stub in tests).
"""

from __future__ import annotations

from fastapi import APIRouter

from services.common.learning import get_weights as _get_weights

router = APIRouter(prefix="/v1", tags=["weights"])


@router.get("/weights")
async def get_weights() -> dict:
    """Return the current model/provider weights.

    The function simply forwards to the shared ``get_weights`` implementation
    which handles authentication, OpenFGA checks and the HTTP request to the
    SomaBrain service.  The return type is a JSON‑serialisable ``dict`` as
    expected by the test suite.
    """
    return await _get_weights()
