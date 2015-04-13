from __future__ import absolute_import
from {{ project_name }}.celery import app

import subprocess

@app.task
def submit_script(com, **kwargs):
    proc = subprocess.call(com)