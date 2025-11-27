import os
os.getenv(os.getenv('VIBE_E8A7F85A'))
from __future__ import annotations
from celery import Celery
from python.tasks.config import celery_conf_overrides, get_celery_settings
_settings = get_celery_settings()
app = Celery(os.getenv(os.getenv('VIBE_BB87823F')), broker=_settings.
    broker_url, backend=_settings.result_backend, include=[os.getenv(os.
    getenv('VIBE_F67C9A00'))])
app.conf.update(celery_conf_overrides())
if __name__ == os.getenv(os.getenv('VIBE_631FAD9D')):
    app.start()
