"""Task serialization helpers for the scheduler system.

This module provides functions to serialize and deserialize task objects
for API responses and persistence.
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any, cast, Dict, Optional, Type, TypeVar, Union

from python.helpers.localization import Localization
from python.helpers.print_style import PrintStyle
from python.helpers.scheduler_models import (
    AdHocTask,
    AnyTask,
    PlannedTask,
    ScheduledTask,
    TaskPlan,
    TaskSchedule,
    TaskState,
)


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Serialize a datetime object to ISO format string in the user's timezone."""
    return Localization.get().serialize_datetime(dt)


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO format datetime string with timezone awareness."""
    if not dt_str:
        return None
    try:
        return Localization.get().localtime_str_to_utc_dt(dt_str)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {dt_str}. Expected ISO format. Error: {e}")


def serialize_task_schedule(schedule: TaskSchedule) -> Dict[str, str]:
    """Convert TaskSchedule to a standardized dictionary format."""
    return {
        "minute": schedule.minute,
        "hour": schedule.hour,
        "day": schedule.day,
        "month": schedule.month,
        "weekday": schedule.weekday,
        "timezone": schedule.timezone,
    }


def parse_task_schedule(schedule_data: Dict[str, str]) -> TaskSchedule:
    """Parse dictionary into TaskSchedule with validation."""
    try:
        return TaskSchedule(
            minute=schedule_data.get("minute", "*"),
            hour=schedule_data.get("hour", "*"),
            day=schedule_data.get("day", "*"),
            month=schedule_data.get("month", "*"),
            weekday=schedule_data.get("weekday", "*"),
            timezone=schedule_data.get("timezone", Localization.get().get_timezone()),
        )
    except Exception as e:
        raise ValueError(f"Invalid schedule format: {e}") from e


def serialize_task_plan(plan: TaskPlan) -> Dict[str, Any]:
    """Convert TaskPlan to a standardized dictionary format."""
    return {
        "todo": [serialize_datetime(dt) for dt in plan.todo],
        "in_progress": (serialize_datetime(plan.in_progress) if plan.in_progress else None),
        "done": [serialize_datetime(dt) for dt in plan.done],
    }


def parse_task_plan(plan_data: Dict[str, Any]) -> TaskPlan:
    """Parse dictionary into TaskPlan with validation."""
    try:
        if not plan_data:
            return TaskPlan(todo=[], in_progress=None, done=[])

        todo_dates = []
        for dt_str in plan_data.get("todo", []):
            if dt_str:
                parsed_dt = parse_datetime(dt_str)
                if parsed_dt:
                    if parsed_dt.tzinfo is None:
                        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                    todo_dates.append(parsed_dt)

        in_progress = None
        if plan_data.get("in_progress"):
            in_progress = parse_datetime(plan_data.get("in_progress"))
            if in_progress and in_progress.tzinfo is None:
                in_progress = in_progress.replace(tzinfo=timezone.utc)

        done_dates = []
        for dt_str in plan_data.get("done", []):
            if dt_str:
                parsed_dt = parse_datetime(dt_str)
                if parsed_dt:
                    if parsed_dt.tzinfo is None:
                        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                    done_dates.append(parsed_dt)

        todo_dates.sort()
        done_dates.sort(reverse=True)

        return TaskPlan.create(
            todo=cast(list[datetime], todo_dates),
            in_progress=in_progress,
            done=cast(list[datetime], done_dates),
        )
    except Exception as e:
        PrintStyle(italic=True, font_color="red", padding=False).print(
            f"Error parsing task plan: {e}"
        )
        return TaskPlan(todo=[], in_progress=None, done=[])


def serialize_task(task: AnyTask) -> Dict[str, Any]:
    """Standardized serialization for task objects."""
    task_dict = {
        "uuid": task.uuid,
        "name": task.name,
        "state": task.state,
        "system_prompt": task.system_prompt,
        "prompt": task.prompt,
        "attachments": task.attachments,
        "created_at": serialize_datetime(task.created_at),
        "updated_at": serialize_datetime(task.updated_at),
        "last_run": serialize_datetime(task.last_run),
        "next_run": serialize_datetime(task.get_next_run()),
        "last_result": task.last_result,
        "context_id": task.context_id,
    }

    if isinstance(task, ScheduledTask):
        task_dict["type"] = "scheduled"
        task_dict["schedule"] = serialize_task_schedule(task.schedule)
    elif isinstance(task, AdHocTask):
        task_dict["type"] = "adhoc"
        task_dict["token"] = task.token
    else:
        task_dict["type"] = "planned"
        task_dict["plan"] = serialize_task_plan(cast(PlannedTask, task).plan)

    return task_dict


def serialize_tasks(tasks: list[AnyTask]) -> list[Dict[str, Any]]:
    """Serialize a list of tasks to a list of dictionaries."""
    return [serialize_task(task) for task in tasks]


T = TypeVar("T", bound=Union[ScheduledTask, AdHocTask, PlannedTask])


def deserialize_task(task_data: Dict[str, Any], task_class: Optional[Type[T]] = None) -> T:
    """Deserialize dictionary into appropriate task object with validation."""
    task_type_str = task_data.get("type", "")
    determined_class = None

    if not task_class:
        if task_type_str == "scheduled":
            determined_class = cast(Type[T], ScheduledTask)
        elif task_type_str == "adhoc":
            determined_class = cast(Type[T], AdHocTask)
            if not task_data.get("token"):
                task_data["token"] = str(random.randint(1000000000000000000, 9999999999999999999))
        elif task_type_str == "planned":
            determined_class = cast(Type[T], PlannedTask)
        else:
            raise ValueError(f"Unknown task type: {task_type_str}")
    else:
        determined_class = task_class
        if determined_class == AdHocTask and not task_data.get("token"):
            task_data["token"] = str(random.randint(1000000000000000000, 9999999999999999999))

    common_args = {
        "uuid": task_data.get("uuid"),
        "name": task_data.get("name"),
        "state": TaskState(task_data.get("state", TaskState.IDLE)),
        "system_prompt": task_data.get("system_prompt", ""),
        "prompt": task_data.get("prompt", ""),
        "attachments": task_data.get("attachments", []),
        "created_at": parse_datetime(task_data.get("created_at")),
        "updated_at": parse_datetime(task_data.get("updated_at")),
        "last_run": parse_datetime(task_data.get("last_run")),
        "last_result": task_data.get("last_result"),
        "context_id": task_data.get("context_id"),
    }

    if determined_class == ScheduledTask:
        schedule_data = task_data.get("schedule", {})
        common_args["schedule"] = parse_task_schedule(schedule_data)
        return ScheduledTask(**common_args)  # type: ignore
    elif determined_class == AdHocTask:
        common_args["token"] = task_data.get("token", "")
        return AdHocTask(**common_args)  # type: ignore
    else:
        plan_data = task_data.get("plan", {})
        common_args["plan"] = parse_task_plan(plan_data)
        return PlannedTask(**common_args)  # type: ignore
