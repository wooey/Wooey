from __future__ import absolute_import
import subprocess
import tarfile
import os
import zipfile
from django.utils.text import get_valid_filename
from django.core.files.storage import default_storage
from django.core.files import File
from django.conf import settings


from celery import Task
from celery import states
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
def submit_script(**kwargs):
    job_id = kwargs.pop('djangui_job')
    resubmit = kwargs.pop('djangui_resubmit', False)
    from .backend import utils
    from .models import DjanguiJob
    job = DjanguiJob.objects.get(pk=job_id)

    command = utils.get_job_commands(job=job)
    if resubmit:
        # clone ourselves, setting pk=None seems hackish but it works
        job.pk = None

    # This is where the script works from -- it is what is after the media_root since that may change between
    # setups/where our user uploads are stored.
    cwd = job.get_output_path()

    abscwd = os.path.abspath(os.path.join(settings.MEDIA_ROOT, cwd))
    job.command = ' '.join(command)
    job.save_path = cwd

    utils.mkdirs(abscwd)
    # make sure we have the script, otherwise download it. This can happen if we have an ephemeral file system or are
    # executing jobs on a worker node.
    script_path = job.script.script_path
    if not utils.get_storage(local=True).exists(script_path.path):
        utils.get_storage(local=True).save(script_path.path, script_path.file)

    job.status = DjanguiJob.RUNNING
    job.save()

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=abscwd)
    stdout, stderr = proc.communicate()
    # tar/zip up the generated content for bulk downloads
    def get_valid_file(cwd, name, ext):
        out = os.path.join(cwd, name)
        index = 0
        while os.path.exists('{}.{}'.format(out, ext)):
            index += 1
            out = os.path.join(cwd, '{}_{}'.format(name, index))
        return '{}.{}'.format(out, ext)

    # fetch the job again in case the database connection was lost during the job or something else changed.
    job = DjanguiJob.objects.get(pk=job_id)

    tar_out = get_valid_file(abscwd, get_valid_filename(job.job_name), 'tar.gz')
    tar = tarfile.open(tar_out, "w:gz")
    tar_name = os.path.splitext(os.path.splitext(os.path.split(tar_out)[1])[0])[0]
    tar.add(abscwd, arcname=tar_name)
    tar.close()


    zip_out = get_valid_file(abscwd, get_valid_filename(job.job_name), 'zip')
    zip = zipfile.ZipFile(zip_out, "w")
    arcname = os.path.splitext(os.path.split(zip_out)[1])[0]
    zip.write(abscwd, arcname=arcname)
    for root, folders, filenames in os.walk(os.path.split(zip_out)[0]):
        for filename in filenames:
            path = os.path.join(root, filename)
            if path == tar_out:
                continue
            if path == zip_out:
                continue
            zip.write(path, arcname=os.path.join(arcname, filename))
    zip.close()


    # save all the files generated as well to our default storage for ephemeral storage setups
    for root, folders, files in os.walk(abscwd):
        for filename in files:
            filepath = os.path.join(root, filename)
            s3path = os.path.join(root[root.find(cwd):], filename)
            exists = utils.get_storage(local=False).exists(s3path)
            filesize = utils.get_storage(local=False).size(s3path)
            if not exists or (exists and filesize == 0):
                if exists:
                    utils.get_storage(local=False).delete(s3path)
                utils.get_storage(local=False).save(s3path, File(open(filepath, 'rb')))

    utils.create_job_fileinfo(job)


    job.stdout = stdout
    job.stderr = stderr
    job.status = DjanguiJob.COMPLETED
    job.save()

    return (stdout, stderr)