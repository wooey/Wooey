__author__ = 'chris'
import json
from collections import OrderedDict

from django.core.urlresolvers import reverse_lazy, reverse
from django.conf import settings
from django import forms
from django.db import transaction
from django.utils.encoding import force_unicode
from django.utils.translation import gettext_lazy as _
from django.db.utils import OperationalError

from ..forms.factory import DJ_FORM_FACTORY

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
            # import ipdb; ipdb.set_trace();
            new_param.value = v
            new_param.save()
            params.append(new_param)
    com = get_script_commands(script=script, parameters=params)
    return job, com


def get_master_form(model=None, pk=None):
    return DJ_FORM_FACTORY.get_master_form(model=model, pk=pk)


def get_form_groups(model=None, pk=None, initial=None):
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
    settings.DJANGUI_APPS = dj_scripts