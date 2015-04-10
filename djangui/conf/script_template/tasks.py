from __future__ import absolute_import
from {{ project_name }}.celery import app

import subprocess

@app.task
def submit_script(com, **kwargs):
    # this doesn't work in here since we lose the filepaths
    # model = kwargs.pop('djangui_model')
    # com = [kwargs.pop('djangui_script_name')]
    # for i,v in kwargs.iteritems():
    #     param = model.get_option_param(i)
    #     if param is None:
    #         continue
    #     if isinstance(v, FieldFile):
    #         com += [param, v.path]
    #     else:
    #         if str(v) == 'True':
    #             com += [param]
    #         elif str(v) == 'False':
    #             continue
    #         else:
    #             com += [param, str(v)]
    # print com
    proc = subprocess.call(com)