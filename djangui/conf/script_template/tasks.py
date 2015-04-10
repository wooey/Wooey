from __future__ import absolute_import
from celery import shared_task
from django.db.models.fields.files import FieldFile

import subprocess

@shared_task
def submit_script(**kwargs):
    model = kwargs.pop('djangui_model')
    com = [kwargs.pop('djangui_script_name')]
    for i,v in kwargs.iteritems():
        param = model.get_option_param(i)
        if param is None:
            continue
        if isinstance(v, FieldFile):
            com += [param, v.path]
        else:
            if str(v) == 'True':
                com += [param]
            elif str(v) == 'False':
                continue
            else:
                com += [param, str(v)]
    print com
    subprocess.call(com)