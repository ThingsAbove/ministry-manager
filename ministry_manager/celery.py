import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministry_manager.settings.local")

app = Celery("ministry_manager")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
