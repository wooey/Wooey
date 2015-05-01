__author__ = 'chris'
import json
import os
from collections import OrderedDict

from django.conf import settings
from django.db import transaction
from django.db.utils import OperationalError
from django.core.files.storage import default_storage

from .argparse_specs import ArgParseNodeBuilder

def sanitize_name(name):
    return name.replace(' ', '_').replace('-', '_')


def sanitize_string(value):
    return value.replace('"', '\\"')


def get_script_commands(script=None, parameters=None):
    com = ['python', script.get_script_path()]
    for param in parameters:
        com.extend(param.get_subprocess_value())
    return com

@transaction.atomic
def create_djangui_job(data):
    from ..models import Script, DjanguiJob, ScriptParameter, ScriptParameters
    script = Script.objects.get(pk=data.get('djangui_type'))
    job = DjanguiJob(user=data.get('user'), job_name=data.get('job_name'), job_description=data.get('job_description'),
                     script=script)
    job.save()
    parameters = {i.slug: i for i in ScriptParameter.objects.filter(slug__in=data.keys())}
    params = []
    for i, v in data.iteritems():
        param = parameters.get(i)
        if param is not None:
            new_param = ScriptParameters(job=job, parameter=param)
            new_param.value = v
            new_param.save()
            params.append(new_param)
    com = get_script_commands(script=script, parameters=params)
    return job, com


def get_master_form(model=None, pk=None):
    from ..forms.factory import DJ_FORM_FACTORY
    return DJ_FORM_FACTORY.get_master_form(model=model, pk=pk)


def get_form_groups(model=None, pk=None, initial=None):
    from ..forms.factory import DJ_FORM_FACTORY
    return DJ_FORM_FACTORY.get_group_forms(model=model, pk=pk, initial=initial)

def load_scripts():
    from ..models import Script
    # select all the scripts we have, then divide them into groups
    dj_scripts = OrderedDict()
    try:
        scripts = Script.objects.count()
    except OperationalError:
        # database not initialized yet
        return
    if scripts:
        scripts = Script.objects.all()
        for script in scripts:
            group = dj_scripts.get(script.script_group.pk, {
                # 'url': reverse_lazy('script_group', kwargs={'script_group', script.script_group.slug}),
                'group': script.script_group, 'scripts': []
            })
            dj_scripts[script.script_group.pk] = group
            # the url mapping is script_group/script_name
            group['scripts'].append(script)
            # might as well load the form here too
            get_master_form(script)
    settings.DJANGUI_SCRIPTS = dj_scripts


def get_storage_object(path):
    # TODO: If we have to add anymore, just make this a class and route the DS methods we need
    obj = default_storage.open(path)
    obj.url = default_storage.url(path)
    obj.path = default_storage.path(path)
    return obj

def add_djangui_script(script=None, group=None, display_name=None):
    from djangui.models import Script, ScriptGroup, ScriptParameter, ScriptParameterGroup
    basename, extension = os.path.splitext(script)
    filename = os.path.split(basename)[1]

    parser = ArgParseNodeBuilder(script_name=filename, script_path=script)
    if not parser.valid:
        return False
    # make our script
    d = parser.get_script_description()
    script_group, created = ScriptGroup.objects.get_or_create(group_name=group)
    djangui_script, created = Script.objects.get_or_create(script_group=script_group, script_description=d['description'],
                                   script_path=script, script_name=display_name if display_name is not None else d['name'])
    if not created:
        djangui_script.script_version += 1
        djangui_script.save()
    # make our parameters
    CHOICE_MAPPING = {

    }
    for param_group_info in d['inputs']:
        param_group, created = ScriptParameterGroup.objects.get_or_create(group_name=param_group_info.get('group'), script=djangui_script)
        for param in param_group_info.get('nodes'):
            # TODO: fix choice limits
            #choice_limit = CHOICE_MAPPING[param.get('choice_limit')]
            # TODO: fix 'file' to be global in argparse
            is_out = True if param.get('upload', None) is False and param.get('type') == 'file' else not param.get('upload', False)
            print param, is_out
            script_param, created = ScriptParameter.objects.get_or_create(script=djangui_script, short_param=param['param'], script_param=param['name'],
                                                  is_output=is_out, required=param.get('required', False),
                                                  form_field=param['model'], default=param.get('default'), input_type=param.get('type'),
                                                  choices=json.dumps(param.get('choices')), choice_limit=None,
                                                  param_help=param.get('help'), is_checked=param.get('checked', False),
                                                  parameter_group=param_group)
    # update our loaded scripts
    load_scripts()