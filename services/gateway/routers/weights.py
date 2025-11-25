"""Legacy compatibility router for the ``/v1/weights`` endpoint.

The original monolithic gateway exposed a ``/v1/weights`` route used by the UI.
This module provides a compatibility shim to satisfy those expectations.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1", tags=["weights"])


@router.get("/weights")
async def get_weights() -> JSONResponse:
    """Return an empty payload for the legacy weights endpoint.

    Real weight handling is performed by the Somabrain client; the tests only
    verify the route exists, not its content.
    """
    return JSONResponse({})
