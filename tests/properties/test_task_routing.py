"""Property 6: Celery task queue routing.

Validates: Requirements 21.1-21.6
Ensures canonical tasks are routed to the expected queues.
"""

import importlib
import os
import sys
import types


def test_celery_task_routes(monkeypatch):
    # Ensure Celery settings resolve without hitting real infra
    redis_url = "redis://localhost:6379/0"
    monkeypatch.setenv("REDIS_URL", redis_url)
    monkeypatch.setenv("CELERY_BROKER_URL", redis_url)
    monkeypatch.setenv("CELERY_RESULT_BACKEND", redis_url)
    monkeypatch.setenv("POSTGRES_DSN", "postgres://user:pass@localhost:5432/db")
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    monkeypatch.setenv("SA01_POLICY_URL", "http://localhost:8181")

    # Stub out heavy dependencies pulled in by python.tasks.a2a_chat_task
    dummy_a2a = types.ModuleType("python.tasks.a2a_chat_task")
    dummy_a2a.a2a_chat_task = None
    sys.modules["python.tasks.a2a_chat_task"] = dummy_a2a
    dummy_fasta = types.ModuleType("python.helpers.fasta2a_client")
    sys.modules["python.helpers.fasta2a_client"] = dummy_fasta

    # Import after env vars are set to avoid cached settings
    app_mod = importlib.import_module("python.tasks.celery_app")
    importlib.reload(app_mod)

    routes = app_mod.app.conf.task_routes

    expected = {
        "python.tasks.core_tasks.delegate": "delegation",
        "python.tasks.core_tasks.build_context": "fast_a2a",
        "python.tasks.core_tasks.evaluate_policy": "fast_a2a",
        "python.tasks.core_tasks.store_interaction": "fast_a2a",
        "python.tasks.core_tasks.feedback_loop": "fast_a2a",
        "python.tasks.core_tasks.rebuild_index": "heavy",
        "python.tasks.core_tasks.publish_metrics": "default",
        "python.tasks.core_tasks.cleanup_sessions": "default",
        "a2a_chat": "fast_a2a",
    }

    # Celery represents routes as mapping task -> dict(queue=...)
    for task, queue in expected.items():
        assert task in routes, f"{task} missing from task_routes"
        assert routes[task]["queue"] == queue, f"{task} should route to {queue}"
