"""Task repository for scheduler persistence.

This module handles task list management and file-based persistence.
"""

from __future__ import annotations

import asyncio
import random
import threading
from os.path import exists
from typing import Annotated, Callable, ClassVar, Optional, Union

from pydantic import BaseModel, Field, PrivateAttr

from python.helpers.files import get_abs_path, make_dirs, read_file, write_file
from python.helpers.print_style import PrintStyle
from python.helpers.scheduler_models import (
    AdHocTask,
    AnyTask,
    PlannedTask,
    ScheduledTask,
    TaskState,
)

SCHEDULER_FOLDER = "tmp/scheduler"


class SchedulerTaskList(BaseModel):
    """Manages the list of scheduled tasks with file-based persistence."""

    tasks: list[
        Annotated[Union[ScheduledTask, AdHocTask, PlannedTask], Field(discriminator="type")]
    ] = Field(default_factory=list)

    __instance: ClassVar[Optional["SchedulerTaskList"]] = PrivateAttr(default=None)

    @classmethod
    def get(cls) -> "SchedulerTaskList":
        path = get_abs_path(SCHEDULER_FOLDER, "tasks.json")
        if cls.__instance is None:
            if not exists(path):
                make_dirs(path)
                cls.__instance = asyncio.run(cls(tasks=[]).save())
            else:
                cls.__instance = cls.model_validate_json(read_file(path))
        else:
            asyncio.run(cls.__instance.reload())
        return cls.__instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lock = threading.RLock()

    async def reload(self) -> "SchedulerTaskList":
        path = get_abs_path(SCHEDULER_FOLDER, "tasks.json")
        if exists(path):
            with self._lock:
                data = self.__class__.model_validate_json(read_file(path))
                self.tasks.clear()
                self.tasks.extend(data.tasks)
        return self

    async def add_task(self, task: AnyTask) -> "SchedulerTaskList":
        with self._lock:
            self.tasks.append(task)
            await self.save()
        return self

    async def save(self) -> "SchedulerTaskList":
        with self._lock:
            # Validate AdHocTasks have valid tokens
            for task in self.tasks:
                if isinstance(task, AdHocTask):
                    if task.token is None or task.token == "":
                        PrintStyle(italic=True, font_color="red", padding=False).print(
                            f"WARNING: AdHocTask {task.name} ({task.uuid}) has null/empty token"
                        )
                        task.token = str(random.randint(1000000000000000000, 9999999999999999999))

            path = get_abs_path(SCHEDULER_FOLDER, "tasks.json")
            if not exists(path):
                make_dirs(path)

            json_data = self.model_dump_json()
            write_file(path, json_data)
        return self

    async def update_task_by_uuid(
        self,
        task_uuid: str,
        updater_func: Callable[[AnyTask], None],
        verify_func: Callable[[AnyTask], bool] = lambda task: True,
    ) -> AnyTask | None:
        """Atomically update a task by UUID using the provided updater function."""
        with self._lock:
            await self.reload()
            task = next(
                (task for task in self.tasks if task.uuid == task_uuid and verify_func(task)),
                None,
            )
            if task is None:
                return None
            updater_func(task)
            await self.save()
            return task

    def get_tasks(self) -> list[AnyTask]:
        with self._lock:
            return self.tasks

    def get_tasks_by_context_id(self, context_id: str, only_running: bool = False) -> list[AnyTask]:
        with self._lock:
            return [
                task
                for task in self.tasks
                if task.context_id == context_id
                and (not only_running or task.state == TaskState.RUNNING)
            ]

    async def get_due_tasks(self) -> list[AnyTask]:
        with self._lock:
            await self.reload()
            return [
                task
                for task in self.tasks
                if task.check_schedule() and task.state == TaskState.IDLE
            ]

    def get_task_by_uuid(self, task_uuid: str) -> AnyTask | None:
        with self._lock:
            return next((task for task in self.tasks if task.uuid == task_uuid), None)

    def get_task_by_name(self, name: str) -> AnyTask | None:
        with self._lock:
            return next((task for task in self.tasks if task.name == name), None)

    def find_task_by_name(self, name: str) -> list[AnyTask]:
        with self._lock:
            return [task for task in self.tasks if name.lower() in task.name.lower()]

    async def remove_task_by_uuid(self, task_uuid: str) -> "SchedulerTaskList":
        with self._lock:
            self.tasks = [task for task in self.tasks if task.uuid != task_uuid]
            await self.save()
        return self

    async def remove_task_by_name(self, name: str) -> "SchedulerTaskList":
        with self._lock:
            self.tasks = [task for task in self.tasks if task.name != name]
            await self.save()
        return self
