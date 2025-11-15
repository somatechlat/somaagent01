"""
Celery app configuration for SomaAgent01.
REAL IMPLEMENTATION - Production-ready Celery configuration.
"""

from __future__ import annotations
import os
from celery import Celery

# REAL IMPLEMENTATION - Celery app configuration
app = Celery(
    'somaagent01',
    broker=os.environ.get('SA01_KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
    backend=os.environ.get('SA01_REDIS_URL', 'redis://redis:6379/0'),
    include=['python.tasks.a2a_chat_task']
)

# REAL IMPLEMENTATION - Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
    result_expires=3600,  # 1 hour
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        }
    }
)

if __name__ == '__main__':
    app.start()