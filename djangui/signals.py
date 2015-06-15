from __future__ import absolute_import

from django.db.models.signals import post_delete
from django.db.utils import InterfaceError, DatabaseError
from django import db

from celery.signals import task_postrun, task_prerun, task_revoked


@task_postrun.connect
@task_prerun.connect
def task_completed(sender=None, **kwargs):
    task_kwargs = kwargs.get('kwargs')
    job_id = task_kwargs.get('djangui_job')
    from .models import DjanguiJob
    from celery import states
    try:
        job = DjanguiJob.objects.get(pk=job_id)
    except (InterfaceError, DatabaseError) as e:
        db.connection.close()
        job = DjanguiJob.objects.get(pk=job_id)
    state = kwargs.get('state')
    if state:
        job.status = DjanguiJob.COMPLETED if state == states.SUCCESS else state
    job.celery_id = kwargs.get('task_id')
    job.save()

def reload_scripts(**kwargs):
    from .backend import utils
    utils.load_scripts()

# TODO: Figure out why relative imports fail here
from .models import Script, ScriptGroup, ScriptParameter, ScriptParameterGroup
post_delete.connect(reload_scripts, sender=Script)
post_delete.connect(reload_scripts, sender=ScriptGroup)
post_delete.connect(reload_scripts, sender=ScriptParameter)
post_delete.connect(reload_scripts, sender=ScriptParameterGroup)