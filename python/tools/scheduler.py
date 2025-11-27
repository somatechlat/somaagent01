import os
import asyncio
import json
import random
import re
from datetime import datetime
from agent import AgentContext
from python.helpers import persist_chat
from python.helpers.task_scheduler import AdHocTask, parse_datetime, PlannedTask, ScheduledTask, serialize_datetime, serialize_task, TaskPlan, TaskSchedule, TaskScheduler, TaskState
from python.helpers.tool import Response, Tool
DEFAULT_WAIT_TIMEOUT = int(os.getenv(os.getenv('VIBE_464D588E')))


class SchedulerTool(Tool):

    async def execute(self, **kwargs):
        if self.method == os.getenv(os.getenv('VIBE_8F50F115')):
            return await self.list_tasks(**kwargs)
        elif self.method == os.getenv(os.getenv('VIBE_C74C45B3')):
            return await self.find_task_by_name(**kwargs)
        elif self.method == os.getenv(os.getenv('VIBE_0DECA0B9')):
            return await self.show_task(**kwargs)
        elif self.method == os.getenv(os.getenv('VIBE_81F77742')):
            return await self.run_task(**kwargs)
        elif self.method == os.getenv(os.getenv('VIBE_C5BB6A0D')):
            return await self.delete_task(**kwargs)
        elif self.method == os.getenv(os.getenv('VIBE_DAE9A252')):
            return await self.create_scheduled_task(**kwargs)
        elif self.method == os.getenv(os.getenv('VIBE_012BF98B')):
            return await self.create_adhoc_task(**kwargs)
        elif self.method == os.getenv(os.getenv('VIBE_2AA7AC05')):
            return await self.create_planned_task(**kwargs)
        elif self.method == os.getenv(os.getenv('VIBE_21ECC8D7')):
            return await self.wait_for_task(**kwargs)
        else:
            return Response(message=
                f"Unknown method '{self.name}:{self.method}'", break_loop=
                int(os.getenv(os.getenv('VIBE_8EA35581'))))

    async def list_tasks(self, **kwargs) ->Response:
        state_filter: list[str] | None = kwargs.get(os.getenv(os.getenv(
            'VIBE_58C236BA')), None)
        type_filter: list[str] | None = kwargs.get(os.getenv(os.getenv(
            'VIBE_33C6D303')), None)
        next_run_within_filter: int | None = kwargs.get(os.getenv(os.getenv
            ('VIBE_427833D4')), None)
        next_run_after_filter: int | None = kwargs.get(os.getenv(os.getenv(
            'VIBE_B6300D8F')), None)
        tasks: list[ScheduledTask | AdHocTask | PlannedTask
            ] = TaskScheduler.get().get_tasks()
        filtered_tasks = []
        for task in tasks:
            if state_filter and task.state not in state_filter:
                continue
            if type_filter and task.type not in type_filter:
                continue
            if next_run_within_filter and task.get_next_run_minutes(
                ) is not None and task.get_next_run_minutes(
                ) > next_run_within_filter:
                continue
            if next_run_after_filter and task.get_next_run_minutes(
                ) is not None and task.get_next_run_minutes(
                ) < next_run_after_filter:
                continue
            filtered_tasks.append(serialize_task(task))
        return Response(message=json.dumps(filtered_tasks, indent=int(os.
            getenv(os.getenv('VIBE_069C2200')))), break_loop=int(os.getenv(
            os.getenv('VIBE_8EA35581'))))

    async def find_task_by_name(self, **kwargs) ->Response:
        name: str = kwargs.get(os.getenv(os.getenv('VIBE_2384227D')), os.
            getenv(os.getenv('VIBE_9024718F')))
        if not name:
            return Response(message=os.getenv(os.getenv('VIBE_00009FA7')),
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        tasks: list[ScheduledTask | AdHocTask | PlannedTask
            ] = TaskScheduler.get().find_task_by_name(name)
        if not tasks:
            return Response(message=f'Task not found: {name}', break_loop=
                int(os.getenv(os.getenv('VIBE_8EA35581'))))
        return Response(message=json.dumps([serialize_task(task) for task in
            tasks], indent=int(os.getenv(os.getenv('VIBE_069C2200')))),
            break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))

    async def show_task(self, **kwargs) ->Response:
        task_uuid: str = kwargs.get(os.getenv(os.getenv('VIBE_5B128598')),
            os.getenv(os.getenv('VIBE_9024718F')))
        if not task_uuid:
            return Response(message=os.getenv(os.getenv('VIBE_4EE7712F')),
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        task: ScheduledTask | AdHocTask | PlannedTask | None = (TaskScheduler
            .get().get_task_by_uuid(task_uuid))
        if not task:
            return Response(message=f'Task not found: {task_uuid}',
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        return Response(message=json.dumps(serialize_task(task), indent=int
            (os.getenv(os.getenv('VIBE_069C2200')))), break_loop=int(os.
            getenv(os.getenv('VIBE_8EA35581'))))

    async def run_task(self, **kwargs) ->Response:
        task_uuid: str = kwargs.get(os.getenv(os.getenv('VIBE_5B128598')),
            os.getenv(os.getenv('VIBE_9024718F')))
        if not task_uuid:
            return Response(message=os.getenv(os.getenv('VIBE_4EE7712F')),
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        task_context: str | None = kwargs.get(os.getenv(os.getenv(
            'VIBE_789E48DE')), None)
        task: ScheduledTask | AdHocTask | PlannedTask | None = (TaskScheduler
            .get().get_task_by_uuid(task_uuid))
        if not task:
            return Response(message=f'Task not found: {task_uuid}',
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        await TaskScheduler.get().run_task_by_uuid(task_uuid, task_context)
        if task.context_id == self.agent.context.id:
            break_loop = int(os.getenv(os.getenv('VIBE_11AE2B85')))
        else:
            break_loop = int(os.getenv(os.getenv('VIBE_8EA35581')))
        return Response(message=f'Task started: {task_uuid}', break_loop=
            break_loop)

    async def delete_task(self, **kwargs) ->Response:
        task_uuid: str = kwargs.get(os.getenv(os.getenv('VIBE_5B128598')),
            os.getenv(os.getenv('VIBE_9024718F')))
        if not task_uuid:
            return Response(message=os.getenv(os.getenv('VIBE_4EE7712F')),
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        task: ScheduledTask | AdHocTask | PlannedTask | None = (TaskScheduler
            .get().get_task_by_uuid(task_uuid))
        if not task:
            return Response(message=f'Task not found: {task_uuid}',
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        context = None
        if task.context_id:
            context = AgentContext.get(task.context_id)
        if task.state == TaskState.RUNNING:
            if context:
                context.reset()
            await TaskScheduler.get().update_task(task_uuid, state=
                TaskState.IDLE)
            await TaskScheduler.get().save()
        if context and context.id == task.uuid:
            AgentContext.remove(context.id)
            persist_chat.remove_chat(context.id)
        await TaskScheduler.get().remove_task_by_uuid(task_uuid)
        if TaskScheduler.get().get_task_by_uuid(task_uuid) is None:
            return Response(message=f'Task deleted: {task_uuid}',
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        else:
            return Response(message=f'Task failed to delete: {task_uuid}',
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))

    async def create_scheduled_task(self, **kwargs) ->Response:
        name: str = kwargs.get(os.getenv(os.getenv('VIBE_2384227D')), os.
            getenv(os.getenv('VIBE_9024718F')))
        system_prompt: str = kwargs.get(os.getenv(os.getenv('VIBE_EEAE105F'
            )), os.getenv(os.getenv('VIBE_9024718F')))
        prompt: str = kwargs.get(os.getenv(os.getenv('VIBE_A0064D55')), os.
            getenv(os.getenv('VIBE_9024718F')))
        attachments: list[str] = kwargs.get(os.getenv(os.getenv(
            'VIBE_DA2CD54F')), [])
        schedule: dict[str, str] = kwargs.get(os.getenv(os.getenv(
            'VIBE_ECB68E7B')), {})
        dedicated_context: bool = kwargs.get(os.getenv(os.getenv(
            'VIBE_75D41BFB')), int(os.getenv(os.getenv('VIBE_8EA35581'))))
        task_schedule = TaskSchedule(minute=schedule.get(os.getenv(os.
            getenv('VIBE_3CA136D2')), os.getenv(os.getenv('VIBE_4C32ED69'))
            ), hour=schedule.get(os.getenv(os.getenv('VIBE_1C3B9CDF')), os.
            getenv(os.getenv('VIBE_4C32ED69'))), day=schedule.get(os.getenv
            (os.getenv('VIBE_30BA6822')), os.getenv(os.getenv(
            'VIBE_4C32ED69'))), month=schedule.get(os.getenv(os.getenv(
            'VIBE_44548357')), os.getenv(os.getenv('VIBE_4C32ED69'))),
            weekday=schedule.get(os.getenv(os.getenv('VIBE_9E43C056')), os.
            getenv(os.getenv('VIBE_4C32ED69'))))
        cron_regex = os.getenv(os.getenv('VIBE_E00C7345'))
        if not re.match(cron_regex, task_schedule.to_crontab()):
            return Response(message=os.getenv(os.getenv('VIBE_AB5E5D8C')) +
                task_schedule.to_crontab(), break_loop=int(os.getenv(os.
                getenv('VIBE_8EA35581'))))
        task = ScheduledTask.create(name=name, system_prompt=system_prompt,
            prompt=prompt, attachments=attachments, schedule=task_schedule,
            context_id=None if dedicated_context else self.agent.context.id)
        await TaskScheduler.get().add_task(task)
        return Response(message=
            f"Scheduled task '{name}' created: {task.uuid}", break_loop=int
            (os.getenv(os.getenv('VIBE_8EA35581'))))

    async def create_adhoc_task(self, **kwargs) ->Response:
        name: str = kwargs.get(os.getenv(os.getenv('VIBE_2384227D')), os.
            getenv(os.getenv('VIBE_9024718F')))
        system_prompt: str = kwargs.get(os.getenv(os.getenv('VIBE_EEAE105F'
            )), os.getenv(os.getenv('VIBE_9024718F')))
        prompt: str = kwargs.get(os.getenv(os.getenv('VIBE_A0064D55')), os.
            getenv(os.getenv('VIBE_9024718F')))
        attachments: list[str] = kwargs.get(os.getenv(os.getenv(
            'VIBE_DA2CD54F')), [])
        token: str = str(random.randint(int(os.getenv(os.getenv(
            'VIBE_90348DF9'))), int(os.getenv(os.getenv('VIBE_CC6086E1')))))
        dedicated_context: bool = kwargs.get(os.getenv(os.getenv(
            'VIBE_75D41BFB')), int(os.getenv(os.getenv('VIBE_8EA35581'))))
        task = AdHocTask.create(name=name, system_prompt=system_prompt,
            prompt=prompt, attachments=attachments, token=token, context_id
            =None if dedicated_context else self.agent.context.id)
        await TaskScheduler.get().add_task(task)
        return Response(message=f"Adhoc task '{name}' created: {task.uuid}",
            break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))

    async def create_planned_task(self, **kwargs) ->Response:
        name: str = kwargs.get(os.getenv(os.getenv('VIBE_2384227D')), os.
            getenv(os.getenv('VIBE_9024718F')))
        system_prompt: str = kwargs.get(os.getenv(os.getenv('VIBE_EEAE105F'
            )), os.getenv(os.getenv('VIBE_9024718F')))
        prompt: str = kwargs.get(os.getenv(os.getenv('VIBE_A0064D55')), os.
            getenv(os.getenv('VIBE_9024718F')))
        attachments: list[str] = kwargs.get(os.getenv(os.getenv(
            'VIBE_DA2CD54F')), [])
        plan: list[str] = kwargs.get(os.getenv(os.getenv('VIBE_8A512D5A')), [])
        dedicated_context: bool = kwargs.get(os.getenv(os.getenv(
            'VIBE_75D41BFB')), int(os.getenv(os.getenv('VIBE_8EA35581'))))
        todo: list[datetime] = []
        for item in plan:
            dt = parse_datetime(item)
            if dt is None:
                return Response(message=f'Invalid datetime: {item}',
                    break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
            todo.append(dt)
        task_plan = TaskPlan.create(todo=todo, in_progress=None, done=[])
        task = PlannedTask.create(name=name, system_prompt=system_prompt,
            prompt=prompt, attachments=attachments, plan=task_plan,
            context_id=None if dedicated_context else self.agent.context.id)
        await TaskScheduler.get().add_task(task)
        return Response(message=
            f"Planned task '{name}' created: {task.uuid}", break_loop=int(
            os.getenv(os.getenv('VIBE_8EA35581'))))

    async def wait_for_task(self, **kwargs) ->Response:
        task_uuid: str = kwargs.get(os.getenv(os.getenv('VIBE_5B128598')),
            os.getenv(os.getenv('VIBE_9024718F')))
        if not task_uuid:
            return Response(message=os.getenv(os.getenv('VIBE_4EE7712F')),
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        scheduler = TaskScheduler.get()
        task: ScheduledTask | AdHocTask | PlannedTask | None = (scheduler.
            get_task_by_uuid(task_uuid))
        if not task:
            return Response(message=f'Task not found: {task_uuid}',
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        if task.context_id == self.agent.context.id:
            return Response(message=os.getenv(os.getenv('VIBE_23A3FFDD')),
                break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
        done = int(os.getenv(os.getenv('VIBE_8EA35581')))
        elapsed = int(os.getenv(os.getenv('VIBE_1528CC47')))
        while not done:
            await scheduler.reload()
            task = scheduler.get_task_by_uuid(task_uuid)
            if not task:
                return Response(message=f'Task not found: {task_uuid}',
                    break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
            if task.state == TaskState.RUNNING:
                await asyncio.sleep(int(os.getenv(os.getenv('VIBE_42CC0C4F'))))
                elapsed += int(os.getenv(os.getenv('VIBE_42CC0C4F')))
                if elapsed > DEFAULT_WAIT_TIMEOUT:
                    return Response(message=
                        f'Task wait timeout ({DEFAULT_WAIT_TIMEOUT} seconds): {task_uuid}'
                        , break_loop=int(os.getenv(os.getenv('VIBE_8EA35581')))
                        )
            else:
                done = int(os.getenv(os.getenv('VIBE_11AE2B85')))
        return Response(message=
            f"""*Task*: {task_uuid}
*State*: {task.state}
*Last run*: {serialize_datetime(task.last_run)}
*Result*:
{task.last_result}"""
            , break_loop=int(os.getenv(os.getenv('VIBE_8EA35581'))))
