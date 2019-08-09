from __future__ import absolute_import
import yaml

from django.db.models.signals import pre_save, post_save
from django.db.utils import InterfaceError, DatabaseError
from django.conf import settings
from django import db

from celery.signals import task_postrun, task_prerun

from .models import ScriptVersion, ScriptParameter, ScriptParameterGroup, ScriptParser, WooeyWidget


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


def skip_script(instance):
    return getattr(instance, '_script_cl_creation', False) or getattr(instance, '_script_upgrade', False) or getattr(instance, '_rename_script', False)


def script_version_presave(instance, **kwargs):
    created = instance.pk is None
    if settings.WOOEY_KUBERNETES:
        if created:
            try:
                yaml.safe_load(stream=instance.kubernetes_manifest)
            except Exception as e:
                print(f"Exception happened: {e}")
    else:
        from .backend import utils
        if not created:
            if 'script_path' in instance.changed_fields and not skip_script(instance):
                # If the script checksum is not changed, do not run the script addition code (but update the
                # path)
                checksum = utils.get_checksum(path=instance.script_path.path)
                if checksum != instance.checksum and not ScriptVersion.objects.filter(checksum=checksum, script_id=instance.script_id).exists():
                    instance.checksum = checksum
                    instance.script_iteration += 1
                    instance._script_upgrade = True
                    instance.pk = None


def script_version_postsave(instance, created, **kwargs):
    if settings.WOOEY_KUBERNETES:
        first_version = ScriptVersion.objects.order_by("id").first()
        if created:
            if first_version.id == instance.id:
                # create one positional param and other staff
                script_name = instance.script.script_name
                sp = ScriptParser(name=script_name)
                sp.save()
                sp.script_version.add(instance)

                spg = ScriptParameterGroup(group_name='Inline arguments')
                spg.save()
                spg.script_version.add(instance)

                widget = WooeyWidget(
                    name='InlineArgs',
                    widget_class='django.forms.TextInput',
                    input_attributes='size="130"'
                )
                widget.save()

                param = ScriptParameter(
                    parser=sp,
                    script_param="arguments",
                    required=False,
                    choices='null',
                    choice_limit='null',
                    form_field="CharField",
                    input_type="text",
                    is_output=True,
                    param_help="Positional and keyword params inline",
                    parameter_group=spg,
                    custom_widget=widget
                )
                param.save()
                param.script_version.add(instance)
            else:
                # assign already existed param to the instance
                sp = ScriptParser.objects.filter(script_version=first_version).first()
                sp.script_version.add(instance)

                spg = ScriptParameterGroup.objects.filter(script_version=first_version).first()
                spg.script_version.add(instance)

                param = ScriptParameter.objects.filter(script_version=first_version).first()
                param.script_version.add(instance)
    else:
        from .backend import utils
        if created and (not skip_script(instance) or getattr(instance, '_script_upgrade', False)):
            res = utils.add_wooey_script(script_version=instance, group=instance.script.script_group)
            instance._script_upgrade = False
            instance._script_cl_creation = False
            instance._rename_script = False
            if res['valid'] == False:
                # delete the model on exceptions.
                instance.delete()
                raise res['errors']
        utils.reset_form_factory(script_version=instance)


pre_save.connect(script_version_presave, sender=ScriptVersion)
post_save.connect(script_version_postsave, sender=ScriptVersion)
