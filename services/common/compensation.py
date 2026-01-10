"""Module compensation."""

from __future__ import annotations

import logging
from typing import Any, Iterable
from uuid import UUID

from prometheus_client import Counter

from services.common.asset_store import AssetStore
from services.common.attachments_store import AttachmentsStore

LOG = logging.getLogger(__name__)

COMP_ACTIONS = Counter(
    "compensation_actions_total",
    "Compensation actions executed",
    labelnames=("action", "result"),
)


async def _delete_attachments(ids: Iterable[Any]) -> None:
    """Execute delete attachments.

        Args:
            ids: The ids.
        """

    store = AttachmentsStore()
    await store.ensure_schema()
    for raw in ids:
        try:
            att_id = UUID(str(raw))
            deleted = await store.delete(att_id)
            COMP_ACTIONS.labels("attachments_delete", "success" if deleted else "not_found").inc()
        except Exception as exc:
            LOG.warning("Attachment compensation failed", extra={"id": raw, "error": str(exc)})
            COMP_ACTIONS.labels("attachments_delete", "failed").inc()


async def _tombstone_assets(ids: Iterable[Any]) -> None:
    """Execute tombstone assets.

        Args:
            ids: The ids.
        """

    store = AssetStore()
    for raw in ids:
        try:
            asset_id = UUID(str(raw))
            ok = await store.tombstone(asset_id, reason="compensation")
            COMP_ACTIONS.labels("assets_tombstone", "success" if ok else "not_found").inc()
        except Exception as exc:
            LOG.warning("Asset compensation failed", extra={"id": raw, "error": str(exc)})
            COMP_ACTIONS.labels("assets_tombstone", "failed").inc()


async def compensate_event(event: dict[str, Any]) -> None:
    """Execute compensate event.

        Args:
            event: The event.
        """

    attachments = event.get("attachments") or []
    assets = event.get("asset_ids") or []
    if attachments:
        await _delete_attachments(attachments)
    if assets:
        await _tombstone_assets(assets)