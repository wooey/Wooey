from __future__ import absolute_import
import subprocess
import tarfile
import os
import zipfile
import importlib

from django.conf import settings
from celery import Task
from celery import app, states

from djguicore.models import DjanguiJob

celery_app = app.app_or_default()

class DjanguiTask(Task):
    pass
    # def after_return(self, status, retval, task_id, args, kwargs, einfo):
    #     job, created = DjanguiJob.objects.get_or_create(djangui_celery_id=task_id)
    #     job.content_type.djangui_celery_state = status
    #     job.save()

@celery_app.task(base=DjanguiTask)
def submit_script(com, **kwargs):
    cwd = kwargs.pop('djangui_cwd')
    proc = subprocess.Popen(com, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    stdout, stderr = proc.communicate()
    # tar/zip up the generated content for bulk downloads
    def get_valid_file(cwd, name, ext):
        out = os.path.join(cwd, name)
        index = 0
        while os.path.exists('{}.{}'.format(out, ext)):
            index += 1
            out = os.path.join(cwd, '{}_{}'.format(name, index))
        return '{}.{}'.format(out, ext)

    out = get_valid_file(cwd, 'djangui_all', 'tar.gz')
    tar = tarfile.open(out, "w:gz")
    tar.add(cwd, arcname=os.path.splitext(os.path.splitext(os.path.split(out)[1])[0])[0])
    tar.close()

    out = get_valid_file(cwd, 'djangui_all', 'zip')
    zip = zipfile.ZipFile(out, "w")
    arcname = os.path.splitext(os.path.split(out)[1])[0]
    zip.write(cwd, arcname=arcname)
    for root, folders, filenames in os.walk(out):
        for filename in filenames:
            zip.write(os.path.join(root, filename), arcname=arcname)


    zip.close()
    return (stdout, stderr)