from __future__ import absolute_import

from celery.signals import task_postrun

@task_postrun.connect
def task_completed(sender=None, **kwargs):
    pass