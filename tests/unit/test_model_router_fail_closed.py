"""Model router must fail closed — never invent a model catalog.

When the LLM ORM registry is unavailable, ``select_model`` must raise
``NoCapableModelError``. Returning fabricated model names would route real
traffic at models nobody provisioned.
"""

from __future__ import annotations

import sys

import pytest

from admin.core.model_router import NoCapableModelError, select_model


@pytest.mark.asyncio
async def test_select_model_raises_when_orm_registry_unavailable():
    """ORM import failure → NoCapableModelError, never a fabricated model."""
    sentinel = object()
    saved = sys.modules.get("admin.llm.models", sentinel)
    # None in sys.modules makes ``from admin.llm.models import ...`` raise
    # ImportError in the real import machinery — the ORM is genuinely
    # unavailable, not replaced by a double.
    sys.modules["admin.llm.models"] = None
    try:
        with pytest.raises(NoCapableModelError) as excinfo:
            await select_model({"text"})
    finally:
        if saved is sentinel:
            sys.modules.pop("admin.llm.models", None)
        else:
            sys.modules["admin.llm.models"] = saved

    message = str(excinfo.value)
    for invented in (
        "gpt-4o",
        "claude-sonnet-4-20250514",
        "gpt-4o-mini",
        "gemini-2.5-flash",
        "llama-3.3-70b",
    ):
        assert invented not in message


@pytest.mark.asyncio
async def test_fabricated_fallback_catalog_is_deleted():
    """The invented model catalog must not exist as a callable or a constant."""
    import admin.core.model_router as model_router

    assert not hasattr(model_router, "_get_fallback_catalog")
    source_names = [
        n
        for n in ("gpt-4o", "gemini-2.5-flash", "llama-3.3-70b")
        if n in open(model_router.__file__, encoding="utf-8").read()
    ]
    assert source_names == [], f"invented model names still present: {source_names}"
