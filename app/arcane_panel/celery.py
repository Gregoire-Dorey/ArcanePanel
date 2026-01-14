import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arcane_panel.settings")

app = Celery("arcane_panel")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "run-checks-every-minute": {
        "task": "core.tasks.run_all_checks",
        "schedule": 60.0,
    }
}
