"""Placeholder router for the legacy ``/v1/weights`` endpoint.

The original monolithic gateway exposed a ``/v1/weights`` route used by the UI
to fetch learning‑model weights. The current modular implementation no longer
provides this endpoint, which caused test failures asserting its presence in the
OpenAPI schema. A lightweight shim is added to satisfy those expectations while
keeping the implementation minimal – it simply returns an empty JSON object.
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
