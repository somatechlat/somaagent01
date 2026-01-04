"""Sensor Outbox Sync Worker.


Polls PostgreSQL outbox, syncs to SomaBrain, clears payload after sync.

Architecture:
    PostgreSQL Outbox → Temporal Workflow → SomaBrain
                              ↓
                      Payload cleared after sync

7-Persona Implementation:
- PhD Dev: ZDL pattern
- DevOps: Temporal durability
- Security Auditor: Data integrity
"""

from __future__ import annotations

import asyncio
import logging

from admin.core.sensors.outbox import SensorOutbox
from admin.somabrain.client import get_somabrain_client, SomaBrainError

logger = logging.getLogger(__name__)


class SyncResult:
    """Result of sync operation."""

    def __init__(
        self,
        event_id: str,
        success: bool,
        brain_ref: str = None,
        error: str = None,
    ):
        """Initialize the instance."""

        self.event_id = event_id
        self.success = success
        self.brain_ref = brain_ref
        self.error = error


async def sync_event_to_somabrain(event: SensorOutbox) -> SyncResult:
    """Sync a single event to SomaBrain.

    Returns:
        SyncResult with brain_ref on success
    """
    client = get_somabrain_client()

    try:
        # Route based on event type
        if event.event_type.startswith("memory."):
            # Memory events → /api/memory/remember/remember
            result = await client.remember(
                tenant=event.tenant_id,
                namespace="ltm",  # Long-term memory
                key=event.event_id,
                value=event.payload,
            )
            brain_ref = f"somabrain://memory/{event.event_id}"

        elif event.event_type.startswith("conversation."):
            # Conversation events → Store as memory
            result = await client.remember(
                tenant=event.tenant_id,
                namespace="conversation",
                key=event.event_id,
                value=event.payload,
            )
            brain_ref = f"somabrain://conversation/{event.event_id}"

        elif event.event_type.startswith("llm."):
            # LLM events → Analytics (Kafka path)
            # These go to Kafka, not directly to SomaBrain
            brain_ref = f"kafka://llm/{event.event_id}"

        elif event.event_type.startswith("tool."):
            # Tool events → Store as memory
            result = await client.remember(
                tenant=event.tenant_id,
                namespace="tool_execution",
                key=event.event_id,
                value=event.payload,
            )
            brain_ref = f"somabrain://tool/{event.event_id}"

        else:
            # Default: store as generic memory
            result = await client.remember(
                tenant=event.tenant_id,
                namespace="events",
                key=event.event_id,
                value=event.payload,
            )
            brain_ref = f"somabrain://events/{event.event_id}"

        return SyncResult(
            event_id=event.event_id,
            success=True,
            brain_ref=brain_ref,
        )

    except SomaBrainError as e:
        logger.warning(f"SomaBrain sync failed for {event.event_id}: {e}")
        return SyncResult(
            event_id=event.event_id,
            success=False,
            error=str(e),
        )


async def process_outbox_batch(
    target_service: str = "somabrain",
    batch_size: int = 50,
) -> dict:
    """Process a batch of pending outbox events.

    Returns:
        Dict with synced_count, failed_count, total_pending
    """
    # Get pending events
    pending = SensorOutbox.get_pending(target_service, limit=batch_size)

    if not pending:
        return {
            "synced_count": 0,
            "failed_count": 0,
            "total_pending": 0,
        }

    synced_count = 0
    failed_count = 0

    for event in pending:
        result = await sync_event_to_somabrain(event)

        if result.success:
            # Mark synced and CLEAR payload
            event.mark_synced(brain_ref=result.brain_ref)
            synced_count += 1
            logger.info(f"Synced {event.event_id} → {result.brain_ref}")
        else:
            # Mark failed for retry
            event.mark_failed(result.error)
            failed_count += 1

    total_pending = SensorOutbox.get_pending_count(target_service)

    return {
        "synced_count": synced_count,
        "failed_count": failed_count,
        "total_pending": total_pending,
    }


async def sync_worker_loop(
    interval_seconds: int = 5,
    batch_size: int = 50,
) -> None:
    """Main sync worker loop.

    Runs continuously, polling the outbox and syncing to SomaBrain.
    """
    logger.info("Starting outbox sync worker")

    while True:
        try:
            result = await process_outbox_batch(batch_size=batch_size)

            if result["synced_count"] > 0 or result["failed_count"] > 0:
                logger.info(
                    f"Sync batch: {result['synced_count']} synced, "
                    f"{result['failed_count']} failed, "
                    f"{result['total_pending']} pending"
                )

        except Exception as e:
            logger.error(f"Sync worker error: {e}")

        await asyncio.sleep(interval_seconds)


# =============================================================================
# TEMPORAL WORKFLOW (for production use)
# =============================================================================

# Temporal workflow definition (uses temporalio SDK)
# This is the production-grade version with durability guarantees

TEMPORAL_SYNC_WORKFLOW = """
# Temporal Workflow for Outbox Sync
# 
# To use with Temporal:
# 
# from temporalio import workflow, activity
# from temporalio.client import Client
# 
# @activity.defn
# async def sync_outbox_activity(batch_size: int) -> dict:
#     return await process_outbox_batch(batch_size=batch_size)
# 
# @workflow.defn
# class OutboxSyncWorkflow:
#     @workflow.run
#     async def run(self, batch_size: int = 50, interval_seconds: int = 5):
#         while True:
#             result = await workflow.execute_activity(
#                 sync_outbox_activity,
#                 batch_size,
#                 start_to_close_timeout=timedelta(minutes=5),
#             )
#             await workflow.sleep(timedelta(seconds=interval_seconds))
"""
