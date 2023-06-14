from __future__ import absolute_import
import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ project_name }}.settings")

app = Celery("{{ project_name }}")

# Using a string here means the worker will not have to
# pickle the object when using Windows.
if "CELERY_CONFIG_MODULE" in os.environ:
    app.config_from_envvar("CELERY_CONFIG_MODULE")
else:
    app.config_from_object("django.conf:settings")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
