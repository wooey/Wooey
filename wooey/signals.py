from __future__ import absolute_import
from functools import wraps

from django.db.models.signals import pre_save, post_save
from django.db.utils import InterfaceError, DatabaseError
from django import db

from celery.signals import task_postrun, task_prerun

from .models import ScriptVersion


def disable_for_loaddata(signal_handler):
    """Function decorator to disable pre_save/post_save functions when
    fixtures are being loaded. The `raw` keyword argument indicates whether
    the model should be save as-is (i.e. when loading a fixture).

    https://docs.djangoproject.com/en/4.0/ref/signals/
    https://stackoverflow.com/a/11409794
    """

    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if not kwargs["raw"]:
            signal_handler(*args, **kwargs)

    return wrapper


@task_postrun.connect
@task_prerun.connect
def task_completed(sender=None, **kwargs):
    task_kwargs = kwargs.get("kwargs")
    job_id = task_kwargs.get("wooey_job")
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
    state = kwargs.get("state")
    if state and job.status not in WooeyJob.TERMINAL_STATES:
        job.status = WooeyJob.COMPLETED if state == states.SUCCESS else state
    job.celery_id = kwargs.get("task_id")
    job.save()


def skip_script(instance):
    return (
        getattr(instance, "_script_cl_creation", False)
        or getattr(instance, "_script_upgrade", False)
        or getattr(instance, "_rename_script", False)
    )


@disable_for_loaddata
def script_version_presave(instance, **kwargs):
    is_updated = instance.pk is not None
    from .backend import utils

    if is_updated:
        # The second filter ensures that in this update, the script_path is being updated. If the script_path in the database
        # matches what is in the current model, we do not carry out this operation. We force a database query here instead
        # of carrying out an in-memory operation to handle multi-server setups.
        if (
            not skip_script(instance)
            and not ScriptVersion.objects.filter(
                pk=instance.pk, script_path=instance.script_path
            ).exists()
        ):
            # If the script checksum is not changed, do not run the script addition code (but update the
            # path)
            checksum = utils.get_checksum(path=instance.script_path.path)
            if (
                checksum != instance.checksum
                and not ScriptVersion.objects.filter(
                    checksum=checksum, script_id=instance.script_id
                ).exists()
            ):
                instance.checksum = checksum
                instance.script_iteration += 1
                instance._script_upgrade = True
                instance.pk = None


@disable_for_loaddata
def script_version_postsave(instance, created, **kwargs):
    from .backend import utils

    if created and (
        not skip_script(instance) or getattr(instance, "_script_upgrade", False)
    ):
        res = utils.add_wooey_script(
            script_version=instance,
            group=instance.script.script_group,
            ignore_bad_imports=instance.script.ignore_bad_imports,
        )
        instance._script_upgrade = False
        instance._script_cl_creation = False
        instance._rename_script = False
        if not res["valid"]:
            # delete the model on exceptions.
            instance.delete()
            raise res["errors"]


pre_save.connect(script_version_presave, sender=ScriptVersion)
post_save.connect(script_version_postsave, sender=ScriptVersion)
