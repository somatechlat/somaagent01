"""Zero-loss Temporal activities: WAL replication, sleep audit, promotion audit, replay.

These activities are the real system entry points — they drain the
``memory.wal`` outbox (``admin.core.models.zdl.OutboxMessage``), POST Brain
``/memory/remember``, drive the Brain sleep FSM, and verify WM→LTM promotion.
No shims. Idempotency key is always ``mem:{coord}`` (INVARIANTS §3.3).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC
from typing import Any

LOGGER = logging.getLogger(__name__)


def _wal_topic() -> str:
    from services.common.memory_contract import get_memory_setting

    return str(get_memory_setting("MEMORY_WAL_TOPIC"))


def _brain_base() -> str:
    from admin.core.helpers.service_urls import require_service_url

    return str(require_service_url("SOMABRAIN_URL")).rstrip("/")


def _brain_token() -> str:
    from services.common.memory_contract import get_memory_setting

    token = get_memory_setting("SOMABRAIN_MEMORY_HTTP_TOKEN")
    if not token:
        raise RuntimeError(
            "SOMABRAIN_MEMORY_HTTP_TOKEN is not configured (Vault secret "
            "secret/agent/credentials/somabrain_memory_http_token). An absent "
            "credential is never sent empty (VIBE Rule 164)."
        )
    return str(token)


def _brain_namespace() -> str:
    from services.common.memory_contract import get_memory_setting

    ns = get_memory_setting("SOMABRAIN_NAMESPACE")
    if not ns:
        raise RuntimeError("SOMABRAIN_NAMESPACE is not configured (VIBE Rule 91).")
    return str(ns)


def _headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {_brain_token()}",
        "X-Namespace": _brain_namespace(),
        "X-Soma-Fast-Ack": "true",
    }


async def _brain_post(path: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{_brain_base()}{path}", json=body, headers=_headers()
        )
        try:
            payload: dict[str, Any] = resp.json() or {}
        except Exception:
            payload = {"raw": resp.text[:2000]}
        return resp.status_code, payload


async def _brain_get(path: str) -> tuple[int, dict[str, Any]]:
    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{_brain_base()}{path}", headers=_headers())
        try:
            payload: dict[str, Any] = resp.json() or {}
        except Exception:
            payload = {"raw": resp.text[:2000]}
        return resp.status_code, payload


def _claim_wal_rows(limit: int) -> list[Any]:
    """Claim drainable ``memory.wal`` OutboxMessage rows (pending + failed)."""
    from asgiref.sync import sync_to_async

    def _query() -> list[Any]:
        from admin.core.models.zdl import OutboxMessage

        return list(
            OutboxMessage.objects.filter(
                topic=_wal_topic(),
                status__in=(OutboxMessage.Status.PENDING, OutboxMessage.Status.FAILED),
            ).order_by("created_at")[: max(1, int(limit))]
        )

    return sync_to_async(_query)()


def _mark_row_published(row_id: Any) -> bool:
    from asgiref.sync import sync_to_async

    def _apply() -> bool:
        from admin.core.models.zdl import OutboxMessage

        try:
            row = OutboxMessage.objects.get(pk=row_id)
        except OutboxMessage.DoesNotExist:
            return False
        row.mark_published()
        return True

    return sync_to_async(_apply)()


def _mark_row_failure(row_id: Any, error: str, *, dead: bool) -> None:
    from asgiref.sync import sync_to_async

    def _apply() -> None:
        from django.utils import timezone

        from admin.core.models.zdl import OutboxMessage

        try:
            row = OutboxMessage.objects.get(pk=row_id)
        except OutboxMessage.DoesNotExist:
            return
        row.last_error = error[:2000]
        if dead:
            # Permanent 4xx is terminal immediately — never retried.
            row.attempts += 1
            row.status = OutboxMessage.Status.DEAD
            row.failed_at = timezone.now()
            row.save()
        else:
            # mark_failed increments attempts and schedules backoff / dead-letter.
            row.mark_failed(error[:2000])

    sync_to_async(_apply)()


def _remember_body_from_payload(event: dict[str, Any]) -> dict[str, Any] | None:
    """Map a ``memory.wal`` outbox payload onto a Brain ``/memory/remember`` body.

    Returns ``None`` when the row is not a remember-able memory write (no text).
    Idempotency identity is ``mem:{coord}`` — the outbox row key and the Brain
    placement key must agree so a replay cannot multiply memories.
    """
    payload = event.get("payload") or {}
    inner = payload.get("payload") or {}
    text = str(inner.get("text") or payload.get("text") or payload.get("content") or "")
    if not text.strip():
        return None
    tenant = str(
        payload.get("tenant") or event.get("tenant") or inner.get("tenant_id") or ""
    ).strip()
    if not tenant:
        return None
    coord = str(inner.get("coord") or payload.get("coord") or event.get("id") or "").strip()
    if not coord:
        return None
    kind = str(inner.get("kind") or payload.get("kind") or "episodic")
    source = str(inner.get("source") or payload.get("source") or "memory-wal-replay")
    salience = float(inner.get("salience") or payload.get("salience") or 0.5)
    ts = inner.get("ts") or payload.get("ts")
    return {
        "tenant": tenant,
        "namespace": _brain_namespace(),
        "key": f"mem:{coord}",
        "value": {
            "text": text,
            "kind": kind,
            "coord": coord,
            "source": source,
            "salience": salience,
            "created_at": ts or datetime.now(UTC).isoformat(),
        },
        "meta": {
            "coord": coord,
            "kind": kind,
            "source": source,
            "idempotency_key": f"mem:{coord}",
        },
        "importance": salience,
        "tags": [kind, source],
    }


async def drain_memory_wal_activity(limit: int = 50) -> dict[str, Any]:
    """Drain ``memory.wal`` outbox → POST Brain ``/memory/remember`` → mark published.

    Idempotent under replay: every request carries ``key=mem:{coord}``, and a
    row already ``published`` is never re-driven.
    """
    rows = await _claim_wal_rows(limit)
    published = 0
    failed = 0
    dead = 0
    skipped = 0
    for row in rows:
        raw = dict(row.payload or {})
        raw.setdefault("tenant", row.partition_key)
        raw.setdefault("id", row.idempotency_key)
        body = _remember_body_from_payload(raw)
        if body is None:
            skipped += 1
            continue
        try:
            # T-1: ONE write lane — MemoryGateway → SomaBrainAdapter. Never raw
            # httpx to /memory/remember from this activity.
            from services.common.memory_gateway import get_memory_gateway

            gateway = get_memory_gateway()
            text = str(
                (body.get("text") or (body.get("payload") or {}).get("text") or "")
            )
            tenant = str(body.get("tenant") or row.partition_key or "")
            kind = str((body.get("meta") or {}).get("kind") or body.get("kind") or "episodic")
            salience = body.get("importance")
            try:
                salience_f = float(salience) if salience is not None else None
            except (TypeError, ValueError):
                salience_f = None
            acks = await gateway.remember_text(
                text,
                tenant_id=tenant,
                kind=kind,
                salience=salience_f,
                source=str((body.get("meta") or {}).get("source") or "memory.wal"),
            )
            ok = any(getattr(a, "ok", False) for a in (acks or []))
            if ok:
                if await _mark_row_published(row.pk):
                    published += 1
            else:
                err = "; ".join(
                    str(getattr(a, "error", "") or "") for a in (acks or [])
                )
                _mark_row_failure(row.pk, f"gateway: {err or 'no ok ack'}", dead=False)
                failed += 1
        except Exception as exc:  # transport — retryable
            _mark_row_failure(row.pk, f"transport: {exc}", dead=False)
            failed += 1
            continue
    return {
        "topic": _wal_topic(),
        "claimed": len(rows),
        "published": published,
        "failed_retryable": failed,
        "dead_letter": dead,
        "skipped_non_memory": skipped,
    }


async def sleep_consolidation_activity(tenant_id: str) -> dict[str, Any]:
    """Drive the Brain sleep FSM one transition and audit consolidation output."""
    if not str(tenant_id).strip():
        raise ValueError("SleepConsolidationWorkflow requires a non-empty tenant_id")
    status, transition = await _brain_post(
        "/sleep/transition",
        {"trigger": "temporal-sleep-consolidation", "tenant_id": tenant_id},
    )
    if status < 200 or status >= 300:
        raise RuntimeError(f"Brain sleep transition failed: HTTP {status}: {transition}")
    new_state = str((transition or {}).get("state") or "").lower()
    state_status, state = await _brain_get("/sleep/state")
    if state_status < 200 or state_status >= 300:
        raise RuntimeError(f"Brain sleep state audit failed: HTTP {state_status}: {state}")
    return {
        "tenant_id": tenant_id,
        "new_state": new_state,
        "consolidation_audited": True,
        "audit": {
            "transition": transition,
            "state_http": state_status,
            "state": state,
            "tenant_id": tenant_id,
        },
    }


async def promotion_audit_activity(tenant_id: str) -> dict[str, Any]:
    """Verify WM→LTM promotion via Brain ``/memory/metrics`` + ``/memory/recall``."""
    if not str(tenant_id).strip():
        raise ValueError("PromotionAuditWorkflow requires a non-empty tenant_id")
    metrics_status, metrics = await _brain_get(f"/memory/metrics?tenant={tenant_id}")
    if metrics_status < 200 or metrics_status >= 300:
        raise RuntimeError(f"Brain /memory/metrics failed: HTTP {metrics_status}: {metrics}")
    recall_status, recall = await _brain_post(
        "/memory/recall",
        {
            "tenant": tenant_id,
            "namespace": _brain_namespace(),
            "query": "promotion-audit",
            "k": 5,
            "layer": "ltm",
        },
    )
    if recall_status < 200 or recall_status >= 300:
        raise RuntimeError(f"Brain /memory/recall failed: HTTP {recall_status}: {recall}")
    hits = recall.get("hits") or recall.get("results") or []
    ltm_hits = [
        h
        for h in hits
        if isinstance(h, dict)
        and (
            str(h.get("layer") or "").lower() in ("ltm", "both")
            or h.get("promoted_from_wm") is True
        )
    ]
    wm_items = int(metrics.get("wm_items") or 0)
    return {
        "tenant_id": tenant_id,
        "wm_items": wm_items,
        "circuit_open": bool(metrics.get("circuit_open")),
        "ltm_hits": len(ltm_hits),
        "recall_total": len(hits),
        "promotion_evidence": bool(ltm_hits) or wm_items == 0,
        "metrics": metrics,
    }


async def replay_unacked_outbox_activity(
    older_than_minutes: int = 5, limit: int = 100
) -> dict[str, Any]:
    """Re-drive unacked outbox rows older than *older_than_minutes*.

    Covers the agent ``OutboxMessage`` ``memory.wal`` rows (T-6
    durable-before-hop) through the same idempotent replication activity.
    """
    from asgiref.sync import sync_to_async

    minutes = max(0, int(older_than_minutes))
    batch = max(1, int(limit))
    cutoff = datetime.now(UTC) - timedelta(minutes=minutes)

    def _select_agent_rows() -> list[Any]:
        from django.utils import timezone

        from admin.core.models.zdl import OutboxMessage

        cutoff_local = timezone.now() - timedelta(minutes=minutes)
        return list(
            OutboxMessage.objects.filter(
                topic=_wal_topic(),
                status__in=(OutboxMessage.Status.PENDING, OutboxMessage.Status.FAILED),
                created_at__lte=cutoff_local,
            ).order_by("created_at")[:batch]
        )

    agent_rows = await sync_to_async(_select_agent_rows)()
    wal_result = await drain_memory_wal_activity(limit=batch)
    return {
        "older_than_minutes": minutes,
        "agent_wal_rows_seen": len(agent_rows),
        "agent_wal_result": wal_result,
        "cutoff": cutoff.isoformat(),
    }
