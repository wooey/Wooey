from __future__ import absolute_import
from celery import shared_task
from django.db.models.fields.files import FieldFile

import subprocess

@shared_task
def submit_script(**kwargs):
    com = [kwargs.pop('djangui_script_name')]
    for i,v in kwargs.iteritems():
        param = '--{0}'.format(i)
        if isinstance(v, FieldFile):
            com += [param, v.path]
        else:
            com += [param, str(v)]
    print com
    subprocess.call(com)