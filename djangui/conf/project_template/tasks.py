from __future__ import absolute_import
import subprocess
import importlib

from django.conf import settings

# TODO: Make this more robust
app = importlib.import_module(settings.DJANGUI_CELERY_APP_NAME).app

@app.task
def submit_script(com, **kwargs):
    proc = subprocess.Popen(com, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return (stdout, stderr)