"""
Celery tasks for SomaAgent01
Handles background processing, cleanup, and scheduled operations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from services.celery_worker.celery_app import celery_app
from services.common.outbox_repository import OutboxStore
from services.common.session_repository import PostgresSessionStore

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def process_long_running_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process long-running background tasks"""
    logger.info(f"Processing {task_type} with data: {task_data}")

    try:
        if task_type == "memory_cleanup":
            return cleanup_memory.delay(task_data)
        elif task_type == "session_export":
            return export_sessions.delay(task_data)
        else:
            return {"status": "error", "message": f"Unknown task type: {task_type}"}
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True)
def cleanup_sessions(self, days_old: int = 30) -> Dict[str, Any]:
    """Clean up old session data"""
    logger.info(f"Cleaning up sessions older than {days_old} days")

    async def _cleanup():
        store = PostgresSessionStore()
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        deleted_count = await store.cleanup_sessions(cutoff_date)
        return {"deleted_sessions": deleted_count, "cutoff_date": str(cutoff_date)}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_cleanup())


@celery_app.task(bind=True)
def export_sessions(self, session_ids: list) -> Dict[str, Any]:
    """Export specific sessions to backup storage"""
    logger.info(f"Exporting {len(session_ids)} sessions")

    async def _export():
        store = PostgresSessionStore()
        exported_count = 0

        for session_id in session_ids:
            try:
                await store.export_session(session_id)
                exported_count += 1
            except Exception as e:
                logger.error(f"Failed to export session {session_id}: {e}")

        return {"exported_sessions": exported_count}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_export())


@celery_app.task(bind=True)
def process_memory_outbox(self) -> Dict[str, Any]:
    """Process memory write outbox"""
    logger.info("Processing memory write outbox")

    async def _process():
        outbox = OutboxStore()
        # Process pending messages in the outbox
        messages = await outbox.claim_batch(limit=100)
        processed_count = len(messages)

        # Mark all as sent (simplified for demo)
        for msg in messages:
            await outbox.mark_sent(msg.id)

        return {"processed_writes": processed_count}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_process())


@celery_app.task(bind=True)
def health_check(self) -> Dict[str, Any]:
    """Periodic health check for all services"""
    logger.info("Running health check")

    async def _check():
        results = {}

        # Check Postgres
        try:
            store = PostgresSessionStore()
            await store.ping()
            results["postgres"] = "ok"
        except Exception as e:
            results["postgres"] = f"error: {str(e)}"

        # Check outbox
        try:
            outbox = OutboxStore()
            # Use claim_batch with limit=0 to test without actually claiming messages
            await outbox.claim_batch(limit=0)
            results["outbox"] = "ok"
        except Exception as e:
            results["outbox"] = f"error: {str(e)}"

        return results

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_check())


@celery_app.task(bind=True)
def process_tool_execution(self, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute tools in background"""
    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

    from services.tool_executor.tool_registry import ToolRegistry

    async def _execute():
        registry = ToolRegistry()
        result = await registry.execute_tool(tool_name, tool_args)
        return {"tool": tool_name, "result": result}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_execute())
