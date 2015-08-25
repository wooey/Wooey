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

def reload_scripts(**kwargs):
    from .backend import utils
    utils.load_scripts()

# TODO: Figure out why relative imports fail here
from .models import Script, ScriptGroup, ScriptParameter, ScriptParameterGroup
post_delete.connect(reload_scripts, sender=Script)
post_delete.connect(reload_scripts, sender=ScriptGroup)
post_delete.connect(reload_scripts, sender=ScriptParameter)
post_delete.connect(reload_scripts, sender=ScriptParameterGroup)

def skip_script(instance):
    return getattr(instance, '_script_cl_creation', False) or getattr(instance, '_script_upgrade', False) or getattr(instance, '_rename_script', False)

def script_presave(instance, **kwargs):
    created = instance.pk is None
    if not created:
        if 'script_path' in instance.changed_fields and not skip_script(instance):
            instance.script_version += 1
            instance._script_upgrade = True
            instance.pk = None

def script_postsave(instance, created, **kwargs):
    from .backend import utils
    if created and (not skip_script(instance) or getattr(instance, '_script_upgrade', False)):
        res = utils.add_wooey_script(script=instance, group=instance.script_group)
        instance._script_upgrade = False
        instance._script_cl_creation = False
        instance._rename_script = False
        if res['valid'] is False:
            # delete the model on exceptions.
            # TODO: use django messages backend to propogate this message to the admin
            instance.delete()
            raise BaseException(res['errors'])
    utils.load_scripts()

pre_save.connect(script_presave, sender=Script)
post_save.connect(script_postsave, sender=Script)
