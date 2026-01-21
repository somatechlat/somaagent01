"""Task models for the scheduler system.

This module contains all Pydantic models for task scheduling:
- TaskSchedule, TaskPlan value objects
- BaseTask, AdHocTask, ScheduledTask, PlannedTask entities

Enums and metrics are imported from scheduler_enums.py.
"""

from __future__ import annotations

import random
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional, Union

import pytz
from crontab import CronTab
from pydantic import BaseModel, Field

from admin.core.helpers.localization import Localization
from admin.core.helpers.scheduler_enums import (
    TaskState,
    TaskType,
    task_schedule_evaluations_total,
    task_schedule_latency_seconds,
)


class TaskSchedule(BaseModel):
    """Taskschedule class implementation."""

    minute: str
    hour: str
    day: str
    month: str
    weekday: str
    timezone: str = Field(default_factory=lambda: Localization.get().get_timezone())

    def to_crontab(self) -> str:
        """Execute to crontab."""

        return f"{self.minute} {self.hour} {self.day} {self.month} {self.weekday}"


class TaskPlan(BaseModel):
    """Taskplan class implementation."""

    todo: list[datetime] = Field(default_factory=list)
    in_progress: datetime | None = None
    done: list[datetime] = Field(default_factory=list)

    @classmethod
    def create(
        cls,
        todo: list[datetime] = list(),
        in_progress: datetime | None = None,
        done: list[datetime] = list(),
    ):
        """Execute create.

        Args:
            todo: The todo.
            in_progress: The in_progress.
            done: The done.
        """

        if todo:
            for idx, dt in enumerate(todo):
                if dt.tzinfo is None:
                    todo[idx] = pytz.timezone("UTC").localize(dt)
        if in_progress:
            if in_progress.tzinfo is None:
                in_progress = pytz.timezone("UTC").localize(in_progress)
        if done:
            for idx, dt in enumerate(done):
                if dt.tzinfo is None:
                    done[idx] = pytz.timezone("UTC").localize(dt)
        return cls(todo=todo, in_progress=in_progress, done=done)

    def add_todo(self, launch_time: datetime):
        """Execute add todo.

        Args:
            launch_time: The launch_time.
        """

        if launch_time.tzinfo is None:
            launch_time = pytz.timezone("UTC").localize(launch_time)
        self.todo.append(launch_time)
        self.todo = sorted(self.todo)

    def set_in_progress(self, launch_time: datetime):
        """Set in progress.

        Args:
            launch_time: The launch_time.
        """

        if launch_time.tzinfo is None:
            launch_time = pytz.timezone("UTC").localize(launch_time)
        if launch_time not in self.todo:
            raise ValueError(f"Launch time {launch_time} not in todo list")
        self.todo.remove(launch_time)
        self.todo = sorted(self.todo)
        self.in_progress = launch_time

    def set_done(self, launch_time: datetime):
        """Set done.

        Args:
            launch_time: The launch_time.
        """

        if launch_time.tzinfo is None:
            launch_time = pytz.timezone("UTC").localize(launch_time)
        if launch_time != self.in_progress:
            raise ValueError(
                f"Launch time {launch_time} is not the same as in progress time {self.in_progress}"
            )
        if launch_time in self.done:
            raise ValueError(f"Launch time {launch_time} already in done list")
        self.in_progress = None
        self.done.append(launch_time)
        self.done = sorted(self.done)

    def get_next_launch_time(self) -> datetime | None:
        """Retrieve next launch time."""

        return self.todo[0] if self.todo else None

    def should_launch(self) -> datetime | None:
        """Execute should launch."""

        next_launch_time = self.get_next_launch_time()
        if next_launch_time is None:
            return None
        if datetime.now(timezone.utc) > next_launch_time:
            return next_launch_time
        return None


class BaseTask(BaseModel):
    """Basetask class implementation."""

    uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context_id: Optional[str] = Field(default=None)
    state: TaskState = Field(default=TaskState.IDLE)
    name: str = Field()
    system_prompt: str
    prompt: str
    attachments: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_run: datetime | None = None
    last_result: str | None = None

    def __init__(self, *args, **kwargs):
        """Initialize the instance."""

        super().__init__(*args, **kwargs)
        if not self.context_id:
            self.context_id = self.uuid
        self._lock = threading.RLock()

    def update(
        self,
        name: str | None = None,
        state: TaskState | None = None,
        system_prompt: str | None = None,
        prompt: str | None = None,
        attachments: list[str] | None = None,
        last_run: datetime | None = None,
        last_result: str | None = None,
        context_id: str | None = None,
        **kwargs,
    ):
        """Execute update.

        Args:
            name: The name.
            state: The state.
            system_prompt: The system_prompt.
            prompt: The prompt.
            attachments: The attachments.
            last_run: The last_run.
            last_result: The last_result.
            context_id: The context_id.
        """

        with self._lock:
            if name is not None:
                self.name = name
                self.updated_at = datetime.now(timezone.utc)
            if state is not None:
                self.state = state
                self.updated_at = datetime.now(timezone.utc)
            if system_prompt is not None:
                self.system_prompt = system_prompt
                self.updated_at = datetime.now(timezone.utc)
            if prompt is not None:
                self.prompt = prompt
                self.updated_at = datetime.now(timezone.utc)
            if attachments is not None:
                self.attachments = attachments
                self.updated_at = datetime.now(timezone.utc)
            if last_run is not None:
                self.last_run = last_run
                self.updated_at = datetime.now(timezone.utc)
            if last_result is not None:
                self.last_result = last_result
                self.updated_at = datetime.now(timezone.utc)
            if context_id is not None:
                self.context_id = context_id
                self.updated_at = datetime.now(timezone.utc)
            for key, value in kwargs.items():
                if value is not None:
                    setattr(self, key, value)
                    self.updated_at = datetime.now(timezone.utc)

    def check_schedule(self, frequency_seconds: float = 60.0) -> bool:
        """Execute check schedule.

        Args:
            frequency_seconds: The frequency_seconds.
        """

        start = time.time()
        try:
            if self.last_run is None:
                result = True
            else:
                elapsed = (datetime.now(timezone.utc) - self.last_run).total_seconds()
                result = elapsed >= frequency_seconds
            task_schedule_evaluations_total.labels(task=self.name).inc()
            task_schedule_latency_seconds.labels(task=self.name).observe(time.time() - start)
            return result
        finally:
            pass

    def get_next_run(self) -> datetime | None:
        """Retrieve next run."""

        if self.last_run is None:
            return datetime.now(timezone.utc)
        return self.last_run + timedelta(seconds=60)

    def get_next_run_minutes(self) -> int | None:
        """Retrieve next run minutes."""

        next_run = self.get_next_run()
        if next_run is None:
            return None
        minutes = int((next_run - datetime.now(timezone.utc)).total_seconds() / 60)
        return max(0, minutes)

    async def on_run(self):
        """Execute on run."""

        pass

    async def on_finish(self):
        """Execute on finish."""

        from admin.core.helpers.task_scheduler import TaskScheduler

        await TaskScheduler.get().update_task(self.uuid, updated_at=datetime.now(timezone.utc))

    async def on_error(self, error: str):
        """Execute on error.

        Args:
            error: The error.
        """

        from admin.core.helpers.print_style import PrintStyle
        from admin.core.helpers.task_scheduler import TaskScheduler

        scheduler = TaskScheduler.get()
        await scheduler.reload()
        updated_task = await scheduler.update_task(
            self.uuid,
            state=TaskState.ERROR,
            last_run=datetime.now(timezone.utc),
            last_result=f"ERROR: {error}",
        )
        if not updated_task:
            PrintStyle(italic=True, font_color="red", padding=False).print(
                f"Failed to update task {self.uuid} state to ERROR after error: {error}"
            )
        await scheduler.save()

    async def on_success(self, result: str):
        """Execute on success.

        Args:
            result: The result.
        """

        from admin.core.helpers.print_style import PrintStyle
        from admin.core.helpers.task_scheduler import TaskScheduler

        scheduler = TaskScheduler.get()
        await scheduler.reload()
        updated_task = await scheduler.update_task(
            self.uuid,
            state=TaskState.IDLE,
            last_run=datetime.now(timezone.utc),
            last_result=result,
        )
        if not updated_task:
            PrintStyle(italic=True, font_color="red", padding=False).print(
                f"Failed to update task {self.uuid} state to IDLE after success"
            )
        await scheduler.save()


class AdHocTask(BaseTask):
    """Adhoctask class implementation."""

    type: Literal[TaskType.AD_HOC] = TaskType.AD_HOC
    token: str = Field(
        default_factory=lambda: str(random.randint(1000000000000000000, 9999999999999999999))
    )

    @classmethod
    def create(
        cls,
        name: str,
        system_prompt: str,
        prompt: str,
        token: str,
        attachments: list[str] = list(),
        context_id: str | None = None,
    ):
        """Execute create.

        Args:
            name: The name.
            system_prompt: The system_prompt.
            prompt: The prompt.
            token: The token.
            attachments: The attachments.
            context_id: The context_id.
        """

        return cls(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            token=token,
            context_id=context_id,
        )

    def update(
        self,
        name: str | None = None,
        state: TaskState | None = None,
        system_prompt: str | None = None,
        prompt: str | None = None,
        attachments: list[str] | None = None,
        last_run: datetime | None = None,
        last_result: str | None = None,
        context_id: str | None = None,
        token: str | None = None,
        **kwargs,
    ):
        """Execute update.

        Args:
            name: The name.
            state: The state.
            system_prompt: The system_prompt.
            prompt: The prompt.
            attachments: The attachments.
            last_run: The last_run.
            last_result: The last_result.
            context_id: The context_id.
            token: The token.
        """

        super().update(
            name=name,
            state=state,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            last_run=last_run,
            last_result=last_result,
            context_id=context_id,
            token=token,
            **kwargs,
        )


class ScheduledTask(BaseTask):
    """Scheduledtask class implementation."""

    type: Literal[TaskType.SCHEDULED] = TaskType.SCHEDULED
    schedule: TaskSchedule

    @classmethod
    def create(
        cls,
        name: str,
        system_prompt: str,
        prompt: str,
        schedule: TaskSchedule,
        attachments: list[str] = list(),
        context_id: str | None = None,
        timezone: str | None = None,
    ):
        """Execute create.

        Args:
            name: The name.
            system_prompt: The system_prompt.
            prompt: The prompt.
            schedule: The schedule.
            attachments: The attachments.
            context_id: The context_id.
            timezone: The timezone.
        """

        if timezone is not None:
            schedule.timezone = timezone
        else:
            schedule.timezone = Localization.get().get_timezone()
        return cls(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            schedule=schedule,
            context_id=context_id,
        )

    def update(
        self,
        name: str | None = None,
        state: TaskState | None = None,
        system_prompt: str | None = None,
        prompt: str | None = None,
        attachments: list[str] | None = None,
        last_run: datetime | None = None,
        last_result: str | None = None,
        context_id: str | None = None,
        schedule: TaskSchedule | None = None,
        **kwargs,
    ):
        """Execute update.

        Args:
            name: The name.
            state: The state.
            system_prompt: The system_prompt.
            prompt: The prompt.
            attachments: The attachments.
            last_run: The last_run.
            last_result: The last_result.
            context_id: The context_id.
            schedule: The schedule.
        """

        super().update(
            name=name,
            state=state,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            last_run=last_run,
            last_result=last_result,
            context_id=context_id,
            schedule=schedule,
            **kwargs,
        )

    def check_schedule(self, frequency_seconds: float = 60.0) -> bool:
        """Execute check schedule.

        Args:
            frequency_seconds: The frequency_seconds.
        """

        with self._lock:
            crontab = CronTab(crontab=self.schedule.to_crontab())
            task_timezone = pytz.timezone(
                self.schedule.timezone or Localization.get().get_timezone()
            )
            reference_time = datetime.now(timezone.utc) - timedelta(seconds=frequency_seconds)
            reference_time = reference_time.astimezone(task_timezone)
            next_run_seconds: Optional[float] = crontab.next(
                now=reference_time, return_datetime=False
            )
            if next_run_seconds is None:
                return False
            return next_run_seconds < frequency_seconds

    def get_next_run(self) -> datetime | None:
        """Retrieve next run."""

        with self._lock:
            crontab = CronTab(crontab=self.schedule.to_crontab())
            return crontab.next(now=datetime.now(timezone.utc), return_datetime=True)


class PlannedTask(BaseTask):
    """Plannedtask class implementation."""

    type: Literal[TaskType.PLANNED] = TaskType.PLANNED
    plan: TaskPlan

    @classmethod
    def create(
        cls,
        name: str,
        system_prompt: str,
        prompt: str,
        plan: TaskPlan,
        attachments: list[str] = list(),
        context_id: str | None = None,
    ):
        """Execute create.

        Args:
            name: The name.
            system_prompt: The system_prompt.
            prompt: The prompt.
            plan: The plan.
            attachments: The attachments.
            context_id: The context_id.
        """

        return cls(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            plan=plan,
            attachments=attachments,
            context_id=context_id,
        )

    def update(
        self,
        name: str | None = None,
        state: TaskState | None = None,
        system_prompt: str | None = None,
        prompt: str | None = None,
        attachments: list[str] | None = None,
        last_run: datetime | None = None,
        last_result: str | None = None,
        context_id: str | None = None,
        plan: TaskPlan | None = None,
        **kwargs,
    ):
        """Execute update.

        Args:
            name: The name.
            state: The state.
            system_prompt: The system_prompt.
            prompt: The prompt.
            attachments: The attachments.
            last_run: The last_run.
            last_result: The last_result.
            context_id: The context_id.
            plan: The plan.
        """

        super().update(
            name=name,
            state=state,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            last_run=last_run,
            last_result=last_result,
            context_id=context_id,
            plan=plan,
            **kwargs,
        )

    def check_schedule(self, frequency_seconds: float = 60.0) -> bool:
        """Execute check schedule.

        Args:
            frequency_seconds: The frequency_seconds.
        """

        with self._lock:
            return self.plan.should_launch() is not None

    def get_next_run(self) -> datetime | None:
        """Retrieve next run."""

        with self._lock:
            return self.plan.get_next_launch_time()

    async def on_run(self):
        """Execute on run."""

        with self._lock:
            next_launch_time = self.plan.should_launch()
            if next_launch_time is not None:
                self.plan.set_in_progress(next_launch_time)
        await super().on_run()

    async def on_finish(self):
        """Execute on finish."""

        from admin.core.helpers.task_scheduler import TaskScheduler

        plan_updated = False
        with self._lock:
            if self.plan.in_progress is not None:
                self.plan.set_done(self.plan.in_progress)
                plan_updated = True
        if plan_updated:
            scheduler = TaskScheduler.get()
            await scheduler.reload()
            await scheduler.update_task(self.uuid, plan=self.plan)
            await scheduler.save()
        await super().on_finish()

    async def on_success(self, result: str):
        """Execute on success.

        Args:
            result: The result.
        """

        await super().on_success(result)

    async def on_error(self, error: str):
        """Execute on error.

        Args:
            error: The error.
        """

        await super().on_error(error)


# Type alias for any task type
AnyTask = Union[ScheduledTask, AdHocTask, PlannedTask]
