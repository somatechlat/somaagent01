"""Thin async client for the Somabrain context‑related endpoints.

The main ``SomaClient`` (see ``python/integrations/soma_client.py``) already
provides a fully‑featured HTTP wrapper with retry, circuit‑breaker and
Prometheus metrics.  This module builds a small façade that exposes only the
operations needed by the ``ContextBuilder`` pipeline:

* ``retrieve`` – POST ``/rag/retrieve``
* ``salience`` – POST ``/context/evaluate`` (returns per‑doc salience scores)
* ``feedback`` – POST ``/context/feedback``

All calls delegate to the singleton ``SomaClient`` instance, preserving the
existing behaviour (timeouts, retries, metrics).  Keeping this thin wrapper
avoids duplication and satisfies the VIBE rule of a **single source of truth**.
"""

from __future__ import annotations

from typing import Any, List, Mapping

from python.integrations.soma_client import SomaClient, SomaClientError

__all__ = ["SomaContextClient", "SomaClientError"]


class SomaContextClient:
    """Convenient wrapper around ``SomaClient`` for context operations.

    The class is deliberately lightweight – it does not maintain its own
    ``httpx.AsyncClient`` but re‑uses the singleton provided by ``SomaClient``.
    This ensures consistent configuration (base URL, API key, timeouts) across
    the whole codebase.
    """

    def __init__(self) -> None:
        # Reuse the shared client; ``SomaClient.get()`` creates it on first use.
        self._client = SomaClient.get()

    # ---------------------------------------------------------------------
    # Retrieval – returns a list of candidate documents for a query.
    # ---------------------------------------------------------------------
    async def retrieve(self, request: Mapping[str, Any], top_k: int) -> List[Mapping[str, Any]]:
        """Call ``/rag/retrieve`` to obtain candidate snippets.

        ``request`` must contain the fields required by the Somabrain API
        (tenant_id, user_id, query, etc.).  ``top_k`` limits the number of
        results.  The method returns the raw JSON list from the ``results`` key
        to keep this client agnostic of the higher‑level ``RetrievedDoc``
        dataclass – ``ContextBuilder`` will perform the conversion.
        """
        payload = {
            "tenant_id": request.get("tenant_id"),
            "user_id": request.get("user_id"),
            "query": request.get("query"),
            "top_k": top_k,
        }
        response = await self._client.rag_retrieve(payload)
        # ``rag_retrieve`` returns the full JSON document; we expect a ``results`` list.
        return response.get("results", [])

    # ---------------------------------------------------------------------
    # Salience – per‑document relevance scores.
    # ---------------------------------------------------------------------
    async def salience(self, doc_ids: List[str], request: Mapping[str, Any]) -> Mapping[str, float]:
        """Call ``/context/evaluate`` to obtain salience scores.

        The Somabrain endpoint expects a payload with ``doc_ids`` and the
        original ``query``.  The response is expected to contain a ``scores``
        mapping of ``doc_id`` → ``float``.  The wrapper returns that mapping
        directly; the caller can fall back to a default score if a key is
        missing.
        """
        payload = {
            "tenant_id": request.get("tenant_id"),
            "query": request.get("query"),
            "doc_ids": doc_ids,
        }
        response = await self._client.context_evaluate(payload)
        return response.get("scores", {})

    # ---------------------------------------------------------------------
    # Feedback – send downstream evaluation of a snippet.
    # ---------------------------------------------------------------------
    async def feedback(self, feedback: Mapping[str, Any]) -> None:
        """Send a feedback record to ``/context/feedback``.

        ``feedback`` should contain the fields required by the API (doc_id,
        tenant_id, success, score, timestamp).  The method does not return a
        value; any HTTP error will raise ``SomaClientError``.
        """
        await self._client.context_feedback(feedback)
