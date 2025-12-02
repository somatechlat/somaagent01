"""Tests for the schedule helper methods in ``python.helpers.task_scheduler``.

These tests verify that the concrete implementations of ``BaseTask.check_schedule``
and ``BaseTask.get_next_run`` behave as expected and that the Prometheus metrics
are updated without raising errors.
"""

import time
from datetime import datetime, timezone, timedelta

import pytest

from python.helpers.task_scheduler import BaseTask, TaskState


def test_check_schedule_never_run_returns_true():
    """A task with ``last_run`` == ``None`` should be considered due."""
    task = BaseTask(
        name="test-task",
        system_prompt="system",
        prompt="prompt",
        state=TaskState.IDLE,
    )
    assert task.last_run is None
    # Frequency is irrelevant when never run
    assert task.check_schedule(frequency_seconds=60) is True


def test_check_schedule_elapsed_time():
    """When ``last_run`` is set, the task is due only after the interval passes."""
    now = datetime.now(timezone.utc)
    task = BaseTask(
        name="test-task",
        system_prompt="system",
        prompt="prompt",
        state=TaskState.IDLE,
        last_run=now - timedelta(seconds=120),
    )
    # 120 s elapsed, interval 60 s → due
    assert task.check_schedule(frequency_seconds=60) is True

    task.last_run = now - timedelta(seconds=30)
    # 30 s elapsed, interval 60 s → not due
    assert task.check_schedule(frequency_seconds=60) is False


def test_get_next_run_behaviour():
    """``get_next_run`` should return ``now`` when never run and ``last_run`` + 60 s otherwise."""
    task = BaseTask(
        name="test-task",
        system_prompt="system",
        prompt="prompt",
        state=TaskState.IDLE,
    )
    now = datetime.now(timezone.utc)
    # When never run, next run is now (allow a small delta)
    nxt = task.get_next_run()
    assert isinstance(nxt, datetime)
    assert abs((nxt - now).total_seconds()) < 1

    # When last_run is set, next run is last_run + 60 seconds
    task.last_run = now - timedelta(seconds=30)
    expected = task.last_run + timedelta(seconds=60)
    assert task.get_next_run() == expected


def test_get_next_run_minutes():
    """Conversion to minutes should be accurate."""
    now = datetime.now(timezone.utc)
    task = BaseTask(
        name="test-task",
        system_prompt="system",
        prompt="prompt",
        state=TaskState.IDLE,
        last_run=now - timedelta(seconds=30),
    )
    # Next run is last_run + 60 s → 30 s from now → 0 minutes (rounded down)
    assert task.get_next_run_minutes() == 0

    # If last_run was 2 minutes ago, next run is 1 minute from now → 1 minute
    task.last_run = now - timedelta(minutes=2)
    assert task.get_next_run_minutes() == 1
