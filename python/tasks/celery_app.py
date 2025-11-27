import os

os.getenv(os.getenv(""))
from __future__ import annotations

from celery import Celery

from python.tasks.config import celery_conf_overrides, get_celery_settings

_settings = get_celery_settings()
app = Celery(
    os.getenv(os.getenv("")),
    broker=_settings.broker_url,
    backend=_settings.result_backend,
    include=[os.getenv(os.getenv(""))],
)
app.conf.update(celery_conf_overrides())
if __name__ == os.getenv(os.getenv("")):
    app.start()
