import asyncio
import logging
from datetime import datetime, timedelta

from celery.schedules import crontab

from services.common.celery_app import celery_app
from services.gateway.utils import redis_scheduler

LOGGER = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self._running = False
        self._task = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        LOGGER.info("SchedulerService started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        LOGGER.info("SchedulerService stopped")

    async def _loop(self):
        LOGGER.info("SchedulerService loop running")
        while self._running:
            try:
                await self._process_tasks()
            except Exception as e:
                LOGGER.error(f"Error in scheduler loop: {e}", exc_info=True)

            # Sleep for 60 seconds
            await asyncio.sleep(60)

    async def _process_tasks(self):
        tasks = await redis_scheduler.list_tasks()
        now = datetime.utcnow()

        for task in tasks:
            if task.get("state") != "enabled":
                continue

            schedule = task.get("schedule")
            if not schedule:
                continue

            # Parse last_run_at
            last_run_iso = task.get("last_run_at")
            if last_run_iso:
                try:
                    # Handle Z suffix if present
                    if last_run_iso.endswith("Z"):
                        last_run_iso = last_run_iso[:-1]
                    last_run_at = datetime.fromisoformat(last_run_iso)
                except ValueError:
                    last_run_at = now - timedelta(minutes=1)
            else:
                # If never run, treat as if run at creation time or now-1m
                created_at_iso = task.get("created_at")
                if created_at_iso:
                    try:
                        if created_at_iso.endswith("Z"):
                            created_at_iso = created_at_iso[:-1]
                        last_run_at = datetime.fromisoformat(created_at_iso)
                    except ValueError:
                        last_run_at = now - timedelta(minutes=1)
                else:
                    last_run_at = now - timedelta(minutes=1)

            # Construct crontab object
            # Filter out None values
            cron_kwargs = {k: v for k, v in schedule.items() if v is not None}
            if not cron_kwargs:
                continue

            try:
                cron = crontab(**cron_kwargs)
                is_due, next_time = cron.is_due(last_run_at)

                if is_due:
                    LOGGER.info(f"Task {task['uuid']} is due. Triggering.")
                    # Trigger task
                    celery_app.send_task("scheduler.run_task", args=[task["uuid"]])

                    # Update last_run_at
                    task["last_run_at"] = now.isoformat() + "Z"
                    await redis_scheduler.save_task(task)
            except Exception as e:
                LOGGER.error(f"Failed to process task {task.get('uuid')}: {e}")


scheduler_service = SchedulerService()
