"""Pydantic models that describe the scheduler API payloads.

These models are used by the FastAPI router to validate incoming JSON from the
web UI and to shape the responses.  The field names match exactly what the UI
expects (see ``webui/js/scheduler.js``).
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """Common fields for a scheduled task."""

    name: str = Field(..., description="Human readable name of the task")
    type: str = Field(..., description="Task type – e.g. 'scheduled' or 'planned'")
    state: str = Field(..., description="Current state – e.g. 'idle', 'running'")
    schedule: Optional[Dict[str, Any]] = Field(
        None, description="Cron‑style schedule definition (minute, hour, …)"
    )
    system_prompt: Optional[str] = Field(None, description="System prompt for LLM tasks")
    prompt: Optional[str] = Field(None, description="User prompt for the task")
    token: Optional[str] = Field(None, description="Auth token if required")
    plan: Optional[Dict[str, Any]] = Field(
        None, description="Optional execution plan (todo/in_progress/done)"
    )
    attachments: List[str] = Field(default_factory=list, description="File IDs attached to the task")


class TaskCreate(TaskBase):
    """Payload for creating a new task – inherits all ``TaskBase`` fields."""


class TaskUpdate(TaskBase):
    """Payload for updating an existing task – requires the UUID of the task."""

    uuid: str = Field(..., description="Unique identifier of the task to update")


class TaskResponse(TaskBase):
    """Full representation of a task as returned by the API."""

    uuid: str = Field(..., description="Unique identifier of the task")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the task was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the task was last modified")


class TaskListResponse(BaseModel):
    """Wrapper returned by ``/scheduler_tasks_list`` – the UI expects a ``tasks`` list."""

    tasks: List[TaskResponse] = Field(default_factory=list)
