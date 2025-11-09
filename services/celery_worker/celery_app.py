"""
Celery application configuration for SomaAgent01
Provides distributed task processing and scheduling
"""
import os
from celery import Celery
from celery.schedules import crontab

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:20001/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:20001/0')

# Create Celery app
celery_app = Celery(
    'somaagent01',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        'services.celery_worker.tasks',
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'services.celery_worker.tasks.*': {'queue': 'default'},
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-sessions': {
            'task': 'services.celery_worker.tasks.cleanup_sessions',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        'health-check': {
            'task': 'services.celery_worker.tasks.health_check',
            'schedule': crontab(minute='*/15'),  # Every 15 minutes
        },
    },
    
    # Retry configuration
    task_annotations={
        'services.celery_worker.tasks.*': {
            'rate_limit': '100/m',
            'max_retries': 3,
            'retry_backoff': True,
        },
    },
)

if __name__ == '__main__':
    celery_app.start()