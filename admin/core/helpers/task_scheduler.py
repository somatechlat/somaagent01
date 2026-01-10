"""Task scheduler for SomaAgent.

This module provides the main TaskScheduler class that orchestrates
task execution. Models, repository, and serialization are in separate modules.
"""

from __future__ import annotations

import asyncio
import os
import uuid
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlparse

import nest_asyncio

nest_asyncio.apply()

from agent import AgentContext, UserMessage
from initialize import initialize_agent

from admin.core.helpers.defer import DeferredTask
from admin.core.helpers.print_style import PrintStyle

# Re-export models for backward compatibility
from admin.core.helpers.scheduler_models import (
    AnyTask,
    TaskState,
)

# Re-export repository
from admin.core.helpers.scheduler_repository import (
    SchedulerTaskList,
)

# Re-export serialization helpers
from admin.core.helpers.scheduler_serialization import (
    serialize_task,
    serialize_tasks,
)
from admin.core.helpers.session_store_adapter import save_context


class TaskScheduler:
    """Main task scheduler that orchestrates task execution."""

    _tasks: SchedulerTaskList
    _printer: PrintStyle
    _instance = None

    @classmethod
    def get(cls) -> "TaskScheduler":
        """Execute get.
            """

        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize the instance."""

        if not hasattr(self, "_initialized"):
            self._tasks = SchedulerTaskList.get()
            self._printer = PrintStyle(italic=True, font_color="green", padding=False)
            self._initialized = True

    async def reload(self):
        """Execute reload.
            """

        await self._tasks.reload()

    def get_tasks(self) -> list[AnyTask]:
        """Retrieve tasks.
            """

        return self._tasks.get_tasks()

    def get_tasks_by_context_id(self, context_id: str, only_running: bool = False) -> list[AnyTask]:
        """Retrieve tasks by context id.

            Args:
                context_id: The context_id.
                only_running: The only_running.
            """

        return self._tasks.get_tasks_by_context_id(context_id, only_running)

    async def add_task(self, task: AnyTask) -> "TaskScheduler":
        """Execute add task.

            Args:
                task: The task.
            """

        await self._tasks.add_task(task)
        await self._get_chat_context(task)
        return self

    async def remove_task_by_uuid(self, task_uuid: str) -> "TaskScheduler":
        """Execute remove task by uuid.

            Args:
                task_uuid: The task_uuid.
            """

        await self._tasks.remove_task_by_uuid(task_uuid)
        return self

    async def remove_task_by_name(self, name: str) -> "TaskScheduler":
        """Execute remove task by name.

            Args:
                name: The name.
            """

        await self._tasks.remove_task_by_name(name)
        return self

    def get_task_by_uuid(self, task_uuid: str) -> AnyTask | None:
        """Retrieve task by uuid.

            Args:
                task_uuid: The task_uuid.
            """

        return self._tasks.get_task_by_uuid(task_uuid)

    def get_task_by_name(self, name: str) -> AnyTask | None:
        """Retrieve task by name.

            Args:
                name: The name.
            """

        return self._tasks.get_task_by_name(name)

    def find_task_by_name(self, name: str) -> list[AnyTask]:
        """Execute find task by name.

            Args:
                name: The name.
            """

        return self._tasks.find_task_by_name(name)

    async def tick(self):
        """Execute tick.
            """

        for task in await self._tasks.get_due_tasks():
            await self._run_task(task)

    async def run_task_by_uuid(self, task_uuid: str, task_context: str | None = None):
        """Execute run task by uuid.

            Args:
                task_uuid: The task_uuid.
                task_context: The task_context.
            """

        await self._tasks.reload()
        task = self.get_task_by_uuid(task_uuid)
        if not task:
            raise ValueError(f"Task with UUID '{task_uuid}' not found")
        if task.state == TaskState.RUNNING:
            raise ValueError(f"Task '{task.name}' is already running")
        if task.state == TaskState.DISABLED:
            raise ValueError(f"Task '{task.name}' is disabled")
        if task.state == TaskState.ERROR:
            self._printer.print(f"Resetting task '{task.name}' from ERROR to IDLE")
            await self.update_task(task_uuid, state=TaskState.IDLE)
            await self._tasks.reload()
            task = self.get_task_by_uuid(task_uuid)
            if not task:
                raise ValueError(f"Task with UUID '{task_uuid}' not found after reset")
        await self._run_task(task, task_context)

    async def run_task_by_name(self, name: str, task_context: str | None = None):
        """Execute run task by name.

            Args:
                name: The name.
                task_context: The task_context.
            """

        task = self._tasks.get_task_by_name(name)
        if task is None:
            raise ValueError(f"Task with name {name} not found")
        await self._run_task(task, task_context)

    async def save(self):
        """Execute save.
            """

        await self._tasks.save()

    async def update_task_checked(
        self,
        task_uuid: str,
        verify_func: Callable[[AnyTask], bool] = lambda task: True,
        **update_params,
    ) -> AnyTask | None:
        """Execute update task checked.

            Args:
                task_uuid: The task_uuid.
                verify_func: The verify_func.
            """

        def _update_task(task):
            """Execute update task.

                Args:
                    task: The task.
                """

            task.update(**update_params)

        return await self._tasks.update_task_by_uuid(task_uuid, _update_task, verify_func)

    async def update_task(self, task_uuid: str, **update_params) -> AnyTask | None:
        """Execute update task.

            Args:
                task_uuid: The task_uuid.
            """

        return await self.update_task_checked(task_uuid, lambda task: True, **update_params)

    async def __new_context(self, task: AnyTask) -> AgentContext:
        """Execute new context.

            Args:
                task: The task.
            """

        if not task.context_id:
            raise ValueError(f"Task {task.name} has no context ID")
        config = initialize_agent()
        context: AgentContext = AgentContext(config, id=task.context_id, name=task.name)
        await save_context(context, reason="scheduler:new_context")
        return context

    async def _get_chat_context(self, task: AnyTask) -> AgentContext:
        """Execute get chat context.

            Args:
                task: The task.
            """

        context = AgentContext.get(task.context_id) if task.context_id else None
        if context:
            assert isinstance(context, AgentContext)
            self._printer.print(f"Scheduler Task {task.name} loaded, context ok")
            await save_context(context, reason="scheduler:reload")
            return context
        else:
            self._printer.print(f"Scheduler Task {task.name} context not found, creating new")
            return await self.__new_context(task)

    async def _checkpoint_session(self, task: AnyTask, context: AgentContext):
        """Execute checkpoint session.

            Args:
                task: The task.
                context: The context.
            """

        if context.id != task.context_id:
            raise ValueError(f"Context ID mismatch: {context.id} != {task.context_id}")
        await save_context(context, reason="scheduler:checkpoint")

    async def _run_task(self, task: AnyTask, task_context: str | None = None):
        """Execute run task.

            Args:
                task: The task.
                task_context: The task_context.
            """

        async def _run_task_wrapper(task_uuid: str, task_context: str | None = None):
            """Execute run task wrapper.

                Args:
                    task_uuid: The task_uuid.
                    task_context: The task_context.
                """

            task_snapshot = self.get_task_by_uuid(task_uuid)
            if task_snapshot is None:
                self._printer.print(f"Task with UUID '{task_uuid}' not found")
                return
            if task_snapshot.state == TaskState.RUNNING:
                self._printer.print(f"Task '{task_snapshot.name}' already running, skipping")
                return

            current_task = await self.update_task_checked(
                task_uuid,
                lambda t: t.state != TaskState.RUNNING,
                state=TaskState.RUNNING,
            )
            if not current_task:
                self._printer.print(f"Task '{task_uuid}' not found or updated by another process")
                return
            if current_task.state != TaskState.RUNNING:
                self._printer.print(f"Task '{current_task.name}' state conflict, skipping")
                return

            await current_task.on_run()
            agent = None

            try:
                self._printer.print(f"Task '{current_task.name}' started")
                context = await self._get_chat_context(current_task)
                agent = context.streaming_agent or context.agent0

                attachment_filenames = []
                if current_task.attachments:
                    for attachment in current_task.attachments:
                        if os.path.exists(attachment):
                            attachment_filenames.append(attachment)
                        else:
                            try:
                                url = urlparse(attachment)
                                if url.scheme in ["http", "https", "ftp", "ftps", "sftp"]:
                                    attachment_filenames.append(attachment)
                            except Exception:
                                self._printer.print(f"Skipping attachment: [{attachment}]")

                self._printer.print(f"User message: {current_task.prompt}")

                if task_context:
                    task_prompt = f"## Context:\n{task_context}\n\n## Task:\n{current_task.prompt}"
                else:
                    task_prompt = f"## Task:\n{current_task.prompt}"

                context.log.log(
                    type="user",
                    heading="User message",
                    content=task_prompt,
                    kvps={"attachments": attachment_filenames},
                    id=str(uuid.uuid4()),
                )

                agent.hist_add_user_message(
                    UserMessage(
                        message=task_prompt,
                        system_message=[current_task.system_prompt],
                        attachments=attachment_filenames,
                    )
                )

                await self._checkpoint_session(current_task, context)
                result = await agent.monologue()

                self._printer.print(f"Task '{current_task.name}' completed: {result}")
                await self._checkpoint_session(current_task, context)
                await current_task.on_success(result)

                await self._tasks.reload()
                updated_task = self.get_task_by_uuid(task_uuid)
                if updated_task and updated_task.state != TaskState.IDLE:
                    await self.update_task(task_uuid, state=TaskState.IDLE)

            except Exception as e:
                self._printer.print(f"Task '{current_task.name}' failed: {e}")
                await current_task.on_error(str(e))

                await self._tasks.reload()
                updated_task = self.get_task_by_uuid(task_uuid)
                if updated_task and updated_task.state != TaskState.ERROR:
                    await self.update_task(task_uuid, state=TaskState.ERROR)

                if agent:
                    agent.handle_critical_exception(e)
            finally:
                await current_task.on_finish()
                await self._tasks.save()

        deferred_task = DeferredTask(thread_name=self.__class__.__name__)
        deferred_task.start_task(_run_task_wrapper, task.uuid, task_context)
        asyncio.create_task(asyncio.sleep(0.1))

    def serialize_all_tasks(self) -> list[Dict[str, Any]]:
        """Execute serialize all tasks.
            """

        return serialize_tasks(self.get_tasks())

    def serialize_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Execute serialize task.

            Args:
                task_id: The task_id.
            """

        task = self.get_task_by_uuid(task_id)
        if task:
            return serialize_task(task)
        return None