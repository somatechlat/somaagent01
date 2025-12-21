"""Describe endpoint: returns a timeline for a session (events + saga states)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from temporalio.client import Client

from integrations.repositories import get_audit_store
from services.common.saga_manager import SagaManager
from services.common.session_repository import PostgresSessionStore
from services.gateway.providers import get_temporal_client
from src.core.config import cfg

router = APIRouter(prefix="/v1/describe", tags=["describe"])


@router.get("/{session_id}")
async def describe_session(
    session_id: str,
    limit: int = Query(200, ge=1, le=1000),
    include_audit: bool = Query(True),
    workflow_id: str | None = Query(None),
    include_workflow: bool = Query(False),
) -> dict:
    """Return session timeline (events) plus recent saga states."""
    store = PostgresSessionStore()
    events = await store.list_events(session_id, limit=limit)

    saga = SagaManager()
    sagas = await saga.list_recent(limit=50)
    related_sagas = [
        s.__dict__
        for s in sagas
        if isinstance(s.data, dict) and s.data.get("session_id") == session_id
    ]
    if workflow_id:
        workflow_sagas = await saga.list_by_workflow(workflow_id, limit=50)
        related_sagas.extend([s.__dict__ for s in workflow_sagas])

    audit_entries = []
    if include_audit:
        try:
            audit_entries = await get_audit_store().list_by_session(session_id, limit=50)
        except Exception:
            audit_entries = []

    workflow_summary = None
    if include_workflow and workflow_id:
        try:
            client = await get_temporal_client()
            handle = client.get_workflow_handle(workflow_id=workflow_id)
            desc = await handle.describe()
            workflow_summary = {
                "workflow_id": workflow_id,
                "run_id": desc.execution.run_id,
                "status": str(desc.status),
                "task_queue": desc.task_queue,
                "history_length": desc.history_length,
            }
        except Exception:
            workflow_summary = {"error": "workflow_describe_failed"}

    if not events and not related_sagas and not audit_entries:
        raise HTTPException(status_code=404, detail="session_not_found")

    return {
        "session_id": session_id,
        "events": events,
        "sagas": related_sagas,
        "audit": audit_entries,
        "workflow": workflow_summary,
    }
