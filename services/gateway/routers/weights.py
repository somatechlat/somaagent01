"""Weights router exposing the SomaBrain learning weights endpoint.

Delegates to ``services.common.learning.get_weights`` which handles
authentication and the HTTP request to SomaBrain.
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
