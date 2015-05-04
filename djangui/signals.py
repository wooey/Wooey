from __future__ import absolute_import

from celery.signals import task_postrun, task_prerun, task_revoked

@task_postrun.connect
@task_prerun.connect
def task_completed(sender=None, **kwargs):
    task_kwargs = kwargs.get('kwargs')
    job_id = task_kwargs.get('djangui_job')
    from .models import DjanguiJob
    job = DjanguiJob.objects.get(pk=job_id)
    state = kwargs.get('state')
    if state:
        job.celery_state = state
    job.celery_id = kwargs.get('task_id')
    job.save()