from __future__ import absolute_import
import subprocess
import importlib

from django.conf import settings
from celery import Task
from celery import app, states

from djguicore.models import DjanguiJob

celery_app = app.app_or_default()

class DjanguiTask(Task):
    pass
    # def after_return(self, status, retval, task_id, args, kwargs, einfo):
    #     job, created = DjanguiJob.objects.get_or_create(djangui_celery_id=task_id)
    #     job.content_type.djangui_celery_state = status
    #     job.save()

@celery_app.task(base=DjanguiTask)
def submit_script(com, **kwargs):
    proc = subprocess.Popen(com, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return (stdout, stderr)