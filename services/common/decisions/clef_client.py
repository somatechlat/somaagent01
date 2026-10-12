"""Clef / Clef-flash client — hosted inference only (no local weights).

``CLEF_BACKEND``:
  * ``workers_ai``    — Cloudflare Workers AI ``/ai/run/{model_id}``
  * ``hf_inference``  — Hugging Face Inference ``/models/{model_id}``

Jev-shaped body (state + questions noul|choice|score). Tokens from Vault only
(``cloudflare_api_key`` or ``huggingface_api_key``). Fail-closed on any missing
input (Rule 1–4, T-5). No mock, no shim, no silent fallback between backends.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from services.common.decisions.contracts import (
    ClefAnswer,
    ClefConfigurationError,
    ClefDecisionError,
    ClefResponse,
)

LOGGER = logging.getLogger(__name__)

# Vendor protocol path templates (not deployment host secrets).
CLEF_AI_RUN_PATH = "/ai/run/{model_id}"
CLEF_HF_PATH = "/models/{model_id}"

_ALLOWED_BACKENDS = frozenset({"workers_ai", "hf_inference"})


def _require_setting(name: str) -> Any:
    from admin.core.helpers.service_urls import require_setting

    try:
        return require_setting(name)
    except Exception as exc:  # noqa: BLE001 — normalize to Clef config error
        raise ClefConfigurationError(f"{name}: {exc}") from exc


def _backend() -> str:
    name = str(_require_setting("CLEF_BACKEND")).strip()
    if name not in _ALLOWED_BACKENDS:
        raise ClefConfigurationError(
            f"CLEF_BACKEND={name!r} is not allowed. "
            f"Set one of: {sorted(_ALLOWED_BACKENDS)}."
        )
    return name


def _vault_token(provider: str, vault_key: str) -> str:
    from services.common.unified_secret_manager import get_secret_manager

    key = get_secret_manager().get_provider_key(provider)
    if not key or key in ("None", "NA"):
        raise ClefConfigurationError(
            f"API token missing for backend provider {provider!r}. "
            f"Set secret/agent/api_keys/{vault_key} in Vault (VIBE Rule 164)."
        )
    return str(key)


def _bearer_for(backend: str) -> str:
    if backend == "hf_inference":
        return _vault_token("huggingface", "huggingface_api_key")
    return _vault_token("cloudflare", "cloudflare_api_key")


def _path_for(backend: str, model_id: str) -> str:
    if backend == "hf_inference":
        return CLEF_HF_PATH.format(model_id=model_id)
    return CLEF_AI_RUN_PATH.format(model_id=model_id)


def _api_base() -> str:
    """API base from settings (operator-managed). No hostname in code."""
    base = str(_require_setting("CLEF_API_BASE")).rstrip("/")
    if not base:
        raise ClefConfigurationError("CLEF_API_BASE is not configured.")
    return base


def _timeout_s() -> float:
    raw = _require_setting("CLEF_TIMEOUT_MS")
    try:
        ms = float(raw)
    except (TypeError, ValueError) as exc:
        raise ClefConfigurationError(f"CLEF_TIMEOUT_MS must be ms, got {raw!r}") from exc
    if ms <= 0:
        raise ClefConfigurationError("CLEF_TIMEOUT_MS must be > 0")
    return ms / 1000.0


class ClefClient:
    """One decide against Workers AI Clef (Jev-compatible System One)."""

    def __init__(
        self,
        *,
        model_id: str | None = None,
        timeout_s: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.backend = _backend()
        self.model_id = str(model_id or _require_setting("CLEF_MODEL_ID")).strip()
        if not self.model_id:
            raise ClefConfigurationError("CLEF_MODEL_ID is not configured.")
        self.timeout_s = float(timeout_s if timeout_s is not None else _timeout_s())
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    def load(self) -> None:
        if self._client is not None:
            return
        self._client = httpx.AsyncClient(
            base_url=_api_base(),
            timeout=self.timeout_s,
            headers={
                "Authorization": f"Bearer {_bearer_for(self.backend)}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            transport=self._transport,
        )

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def decide(self, *, state: Any, questions: dict[str, Any]) -> ClefResponse:
        """POST Jev-shaped decision request. Raises ClefDecisionError on failure."""
        self.load()
        assert self._client is not None
        body = {
            "model": self.model_id,
            "state": state,
            "questions": questions,
        }
        path = _path_for(self.backend, self.model_id)
        started = time.perf_counter()
        try:
            resp = await self._client.post(path, json=body)
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException as exc:
            raise ClefDecisionError(f"Clef timeout after {self.timeout_s:.3f}s") from exc
        except httpx.HTTPError as exc:
            raise ClefDecisionError(f"Clef HTTP error: {exc}") from exc
        except ValueError as exc:
            raise ClefDecisionError(f"Clef returned non-JSON: {exc}") from exc

        latency_ms = (time.perf_counter() - started) * 1000.0
        return self._parse(data, latency_ms=latency_ms)

    def _parse(self, data: Any, *, latency_ms: float) -> ClefResponse:
        if not isinstance(data, dict):
            raise ClefDecisionError("Clef response is not an object")
        # Workers AI may wrap the Jev payload in `result`.
        payload = data.get("result") if isinstance(data.get("result"), dict) else data
        raw_answers = payload.get("answers") or {}
        if not raw_answers:
            raise ClefDecisionError("Clef response missing answers")
        answers: dict[str, ClefAnswer] = {}
        for qid, raw in raw_answers.items():
            try:
                answers[str(qid)] = ClefAnswer.model_validate(raw)
            except Exception as exc:  # noqa: BLE001
                raise ClefDecisionError(f"Clef answer {qid!r} invalid: {exc}") from exc
        model = str(payload.get("model") or self.model_id)
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else None
        return ClefResponse(
            model=model,
            answers=answers,
            latency_ms=float(payload.get("latency_ms") or latency_ms),
            usage=usage,
        )


__all__ = ["ClefClient", "CLEF_AI_RUN_PATH"]
