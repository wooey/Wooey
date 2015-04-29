from __future__ import absolute_import
import subprocess
import tarfile
import os
import zipfile


from celery import Task
from celery import app
from celery.contrib import rdb

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

    tar_out = get_valid_file(cwd, 'djangui_all', 'tar.gz')
    tar = tarfile.open(tar_out, "w:gz")
    tar.add(cwd, arcname=os.path.splitext(os.path.splitext(os.path.split(tar_out)[1])[0])[0])
    tar.close()

    zip_out = get_valid_file(cwd, 'djangui_all', 'zip')
    zip = zipfile.ZipFile(zip_out, "w")
    arcname = os.path.splitext(os.path.split(zip_out)[1])[0]
    zip.write(cwd, arcname=arcname)
    for root, folders, filenames in os.walk(os.path.split(zip_out)[0]):
        for filename in filenames:
            path = os.path.join(root, filename)
            if path == tar_out:
                continue
            if path == zip_out:
                continue
            zip.write(path, arcname=os.path.join(arcname, filename))
    zip.close()

    return (stdout, stderr)