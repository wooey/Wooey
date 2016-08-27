from __future__ import absolute_import

from django.db.models.signals import post_delete, pre_save, post_save
from django.db.utils import InterfaceError, DatabaseError
from django import db

from celery.signals import task_postrun, task_prerun, task_revoked


@task_postrun.connect
@task_prerun.connect
def task_completed(sender=None, **kwargs):
    task_kwargs = kwargs.get('kwargs')
    job_id = task_kwargs.get('wooey_job')
    # Just return if it is not a wooey_job!
    if not job_id:
        return

    from .models import WooeyJob
    from celery import states
    try:
        job = WooeyJob.objects.get(pk=job_id)
    except (InterfaceError, DatabaseError) as e:
        db.connection.close()
        job = WooeyJob.objects.get(pk=job_id)
    state = kwargs.get('state')
    if state:
        job.status = WooeyJob.COMPLETED if state == states.SUCCESS else state
    job.celery_id = kwargs.get('task_id')
    job.save()

from .models import ScriptVersion


def skip_script(instance):
    return getattr(instance, '_script_cl_creation', False) or getattr(instance, '_script_upgrade', False) or getattr(instance, '_rename_script', False)


def script_version_presave(instance, **kwargs):
    created = instance.pk is None
    if not created:
        if 'script_path' in instance.changed_fields and not skip_script(instance):
            instance.script_iteration += 1
            instance._script_upgrade = True
            instance.pk = None


def script_version_postsave(instance, created, **kwargs):
    from .backend import utils
    if created and (not skip_script(instance) or getattr(instance, '_script_upgrade', False)):
        res = utils.add_wooey_script(script_version=instance, group=instance.script.script_group)
        instance._script_upgrade = False
        instance._script_cl_creation = False
        instance._rename_script = False
        if res['valid'] == False:
            # delete the model on exceptions.
            # TODO: use django messages backend to propogate this message to the admin
            instance.delete()
            raise BaseException(res['errors'])
    utils.reset_form_factory(script_version=instance)

pre_save.connect(script_version_presave, sender=ScriptVersion)
post_save.connect(script_version_postsave, sender=ScriptVersion)
