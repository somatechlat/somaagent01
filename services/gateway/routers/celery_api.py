"""FastAPI router to enqueue Celery tasks and query status."""

from __future__ import annotations

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.celery_worker import celery_app

router = APIRouter(prefix="/v1/celery", tags=["celery"])


class TaskRequest(BaseModel):
    task: str
    payload: dict


@router.post("/run")
async def run_task(req: TaskRequest) -> dict:
    if req.task not in celery_app.tasks:
        raise HTTPException(status_code=404, detail="unknown_task")
    async_result = celery_app.send_task(req.task, args=[req.payload])
    return {"task_id": async_result.id, "status": async_result.status}


@router.get("/runs/{task_id}")
async def get_status(task_id: str) -> dict:
    result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": result.status, "result": result.result if result.successful() else None}
