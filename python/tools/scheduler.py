import asyncio
import json
import os
import random
import re
from datetime import datetime

from agent import AgentContext
from python.helpers import persist_chat
from python.helpers.task_scheduler import (
    AdHocTask,
    parse_datetime,
    PlannedTask,
    ScheduledTask,
    serialize_datetime,
    serialize_task,
    TaskPlan,
    TaskSchedule,
    TaskScheduler,
    TaskState,
)
from python.helpers.tool import Response, Tool

DEFAULT_WAIT_TIMEOUT = int(os.getenv(os.getenv("")))


class SchedulerTool(Tool):

    async def execute(self, **kwargs):
        if self.method == os.getenv(os.getenv("")):
            return await self.list_tasks(**kwargs)
        elif self.method == os.getenv(os.getenv("")):
            return await self.find_task_by_name(**kwargs)
        elif self.method == os.getenv(os.getenv("")):
            return await self.show_task(**kwargs)
        elif self.method == os.getenv(os.getenv("")):
            return await self.run_task(**kwargs)
        elif self.method == os.getenv(os.getenv("")):
            return await self.delete_task(**kwargs)
        elif self.method == os.getenv(os.getenv("")):
            return await self.create_scheduled_task(**kwargs)
        elif self.method == os.getenv(os.getenv("")):
            return await self.create_adhoc_task(**kwargs)
        elif self.method == os.getenv(os.getenv("")):
            return await self.create_planned_task(**kwargs)
        elif self.method == os.getenv(os.getenv("")):
            return await self.wait_for_task(**kwargs)
        else:
            return Response(
                message=f"Unknown method '{self.name}:{self.method}'",
                break_loop=int(os.getenv(os.getenv(""))),
            )

    async def list_tasks(self, **kwargs) -> Response:
        state_filter: list[str] | None = kwargs.get(os.getenv(os.getenv("")), None)
        type_filter: list[str] | None = kwargs.get(os.getenv(os.getenv("")), None)
        next_run_within_filter: int | None = kwargs.get(os.getenv(os.getenv("")), None)
        next_run_after_filter: int | None = kwargs.get(os.getenv(os.getenv("")), None)
        tasks: list[ScheduledTask | AdHocTask | PlannedTask] = TaskScheduler.get().get_tasks()
        filtered_tasks = []
        for task in tasks:
            if state_filter and task.state not in state_filter:
                continue
            if type_filter and task.type not in type_filter:
                continue
            if (
                next_run_within_filter
                and task.get_next_run_minutes() is not None
                and (task.get_next_run_minutes() > next_run_within_filter)
            ):
                continue
            if (
                next_run_after_filter
                and task.get_next_run_minutes() is not None
                and (task.get_next_run_minutes() < next_run_after_filter)
            ):
                continue
            filtered_tasks.append(serialize_task(task))
        return Response(
            message=json.dumps(filtered_tasks, indent=int(os.getenv(os.getenv("")))),
            break_loop=int(os.getenv(os.getenv(""))),
        )

    async def find_task_by_name(self, **kwargs) -> Response:
        name: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        if not name:
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        tasks: list[ScheduledTask | AdHocTask | PlannedTask] = (
            TaskScheduler.get().find_task_by_name(name)
        )
        if not tasks:
            return Response(
                message=f"Task not found: {name}", break_loop=int(os.getenv(os.getenv("")))
            )
        return Response(
            message=json.dumps(
                [serialize_task(task) for task in tasks], indent=int(os.getenv(os.getenv("")))
            ),
            break_loop=int(os.getenv(os.getenv(""))),
        )

    async def show_task(self, **kwargs) -> Response:
        task_uuid: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        if not task_uuid:
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        task: ScheduledTask | AdHocTask | PlannedTask | None = TaskScheduler.get().get_task_by_uuid(
            task_uuid
        )
        if not task:
            return Response(
                message=f"Task not found: {task_uuid}", break_loop=int(os.getenv(os.getenv("")))
            )
        return Response(
            message=json.dumps(serialize_task(task), indent=int(os.getenv(os.getenv("")))),
            break_loop=int(os.getenv(os.getenv(""))),
        )

    async def run_task(self, **kwargs) -> Response:
        task_uuid: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        if not task_uuid:
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        task_context: str | None = kwargs.get(os.getenv(os.getenv("")), None)
        task: ScheduledTask | AdHocTask | PlannedTask | None = TaskScheduler.get().get_task_by_uuid(
            task_uuid
        )
        if not task:
            return Response(
                message=f"Task not found: {task_uuid}", break_loop=int(os.getenv(os.getenv("")))
            )
        await TaskScheduler.get().run_task_by_uuid(task_uuid, task_context)
        if task.context_id == self.agent.context.id:
            break_loop = int(os.getenv(os.getenv("")))
        else:
            break_loop = int(os.getenv(os.getenv("")))
        return Response(message=f"Task started: {task_uuid}", break_loop=break_loop)

    async def delete_task(self, **kwargs) -> Response:
        task_uuid: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        if not task_uuid:
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        task: ScheduledTask | AdHocTask | PlannedTask | None = TaskScheduler.get().get_task_by_uuid(
            task_uuid
        )
        if not task:
            return Response(
                message=f"Task not found: {task_uuid}", break_loop=int(os.getenv(os.getenv("")))
            )
        context = None
        if task.context_id:
            context = AgentContext.get(task.context_id)
        if task.state == TaskState.RUNNING:
            if context:
                context.reset()
            await TaskScheduler.get().update_task(task_uuid, state=TaskState.IDLE)
            await TaskScheduler.get().save()
        if context and context.id == task.uuid:
            AgentContext.remove(context.id)
            persist_chat.remove_chat(context.id)
        await TaskScheduler.get().remove_task_by_uuid(task_uuid)
        if TaskScheduler.get().get_task_by_uuid(task_uuid) is None:
            return Response(
                message=f"Task deleted: {task_uuid}", break_loop=int(os.getenv(os.getenv("")))
            )
        else:
            return Response(
                message=f"Task failed to delete: {task_uuid}",
                break_loop=int(os.getenv(os.getenv(""))),
            )

    async def create_scheduled_task(self, **kwargs) -> Response:
        name: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        system_prompt: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        prompt: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        attachments: list[str] = kwargs.get(os.getenv(os.getenv("")), [])
        schedule: dict[str, str] = kwargs.get(os.getenv(os.getenv("")), {})
        dedicated_context: bool = kwargs.get(
            os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))
        )
        task_schedule = TaskSchedule(
            minute=schedule.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))),
            hour=schedule.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))),
            day=schedule.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))),
            month=schedule.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))),
            weekday=schedule.get(os.getenv(os.getenv("")), os.getenv(os.getenv(""))),
        )
        cron_regex = os.getenv(os.getenv(""))
        if not re.match(cron_regex, task_schedule.to_crontab()):
            return Response(
                message=os.getenv(os.getenv("")) + task_schedule.to_crontab(),
                break_loop=int(os.getenv(os.getenv(""))),
            )
        task = ScheduledTask.create(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            schedule=task_schedule,
            context_id=None if dedicated_context else self.agent.context.id,
        )
        await TaskScheduler.get().add_task(task)
        return Response(
            message=f"Scheduled task '{name}' created: {task.uuid}",
            break_loop=int(os.getenv(os.getenv(""))),
        )

    async def create_adhoc_task(self, **kwargs) -> Response:
        name: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        system_prompt: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        prompt: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        attachments: list[str] = kwargs.get(os.getenv(os.getenv("")), [])
        token: str = str(
            random.randint(int(os.getenv(os.getenv(""))), int(os.getenv(os.getenv(""))))
        )
        dedicated_context: bool = kwargs.get(
            os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))
        )
        task = AdHocTask.create(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            token=token,
            context_id=None if dedicated_context else self.agent.context.id,
        )
        await TaskScheduler.get().add_task(task)
        return Response(
            message=f"Adhoc task '{name}' created: {task.uuid}",
            break_loop=int(os.getenv(os.getenv(""))),
        )

    async def create_planned_task(self, **kwargs) -> Response:
        name: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        system_prompt: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        prompt: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        attachments: list[str] = kwargs.get(os.getenv(os.getenv("")), [])
        plan: list[str] = kwargs.get(os.getenv(os.getenv("")), [])
        dedicated_context: bool = kwargs.get(
            os.getenv(os.getenv("")), int(os.getenv(os.getenv("")))
        )
        todo: list[datetime] = []
        for item in plan:
            dt = parse_datetime(item)
            if dt is None:
                return Response(
                    message=f"Invalid datetime: {item}", break_loop=int(os.getenv(os.getenv("")))
                )
            todo.append(dt)
        task_plan = TaskPlan.create(todo=todo, in_progress=None, done=[])
        task = PlannedTask.create(
            name=name,
            system_prompt=system_prompt,
            prompt=prompt,
            attachments=attachments,
            plan=task_plan,
            context_id=None if dedicated_context else self.agent.context.id,
        )
        await TaskScheduler.get().add_task(task)
        return Response(
            message=f"Planned task '{name}' created: {task.uuid}",
            break_loop=int(os.getenv(os.getenv(""))),
        )

    async def wait_for_task(self, **kwargs) -> Response:
        task_uuid: str = kwargs.get(os.getenv(os.getenv("")), os.getenv(os.getenv("")))
        if not task_uuid:
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        scheduler = TaskScheduler.get()
        task: ScheduledTask | AdHocTask | PlannedTask | None = scheduler.get_task_by_uuid(task_uuid)
        if not task:
            return Response(
                message=f"Task not found: {task_uuid}", break_loop=int(os.getenv(os.getenv("")))
            )
        if task.context_id == self.agent.context.id:
            return Response(
                message=os.getenv(os.getenv("")), break_loop=int(os.getenv(os.getenv("")))
            )
        done = int(os.getenv(os.getenv("")))
        elapsed = int(os.getenv(os.getenv("")))
        while not done:
            await scheduler.reload()
            task = scheduler.get_task_by_uuid(task_uuid)
            if not task:
                return Response(
                    message=f"Task not found: {task_uuid}", break_loop=int(os.getenv(os.getenv("")))
                )
            if task.state == TaskState.RUNNING:
                await asyncio.sleep(int(os.getenv(os.getenv(""))))
                elapsed += int(os.getenv(os.getenv("")))
                if elapsed > DEFAULT_WAIT_TIMEOUT:
                    return Response(
                        message=f"Task wait timeout ({DEFAULT_WAIT_TIMEOUT} seconds): {task_uuid}",
                        break_loop=int(os.getenv(os.getenv(""))),
                    )
            else:
                done = int(os.getenv(os.getenv("")))
        return Response(
            message=f"*Task*: {task_uuid}\n*State*: {task.state}\n*Last run*: {serialize_datetime(task.last_run)}\n*Result*:\n{task.last_result}",
            break_loop=int(os.getenv(os.getenv(""))),
        )
