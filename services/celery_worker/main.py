"""
Celery worker main entry point
"""

import logging

from services.celery_worker.celery_app import celery_app

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    # Start Celery worker
    celery_app.worker_main(
        [
            "--loglevel=INFO",
            "--hostname=somaagent01-celery@%h",
            "--queues=default",
            "--concurrency=4",
        ]
    )
