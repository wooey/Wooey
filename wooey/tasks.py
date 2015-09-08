from __future__ import absolute_import
import subprocess
import tarfile
import os
import zipfile
import six
import traceback
import time

from django.utils.text import get_valid_filename
from django.core.files.storage import default_storage
from django.core.files import File
from django.conf import settings
from django.db.transaction import atomic

from celery import Task
from celery import states
from celery import app
from celery.signals import worker_process_init
from celery.contrib import rdb

from . import settings as wooey_settings

celery_app = app.app_or_default()

@worker_process_init.connect
def configure_workers(*args, **kwargs):
    # this sets up Django on nodes started by the worker daemon.
    import django
    django.setup()


class WooeyTask(Task):
    pass

    # def after_return(self, status, retval, task_id, args, kwargs, einfo):
    #     job, created = WooeyJob.objects.get_or_create(wooey_celery_id=task_id)
    #     job.content_type.wooey_celery_state = status
    #     job.save()

@celery_app.task(base=WooeyTask)
def submit_script(**kwargs):
    job_id = kwargs.pop('wooey_job')
    resubmit = kwargs.pop('wooey_resubmit', False)
    from .backend import utils
    from .models import WooeyJob, WooeyFile
    job = WooeyJob.objects.get(pk=job_id)

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
    script_path = job.script_version.script_path
    if not utils.get_storage(local=True).exists(script_path.path):
        utils.get_storage(local=True).save(script_path.path, script_path.file)

    job.status = WooeyJob.RUNNING
    job.save()

    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=abscwd)

    stdout, stderr = proc.communicate()

    # tar/zip up the generated content for bulk downloads
    def get_valid_file(cwd, name, ext):
        out = os.path.join(cwd, name)
        index = 0
        while os.path.exists(six.u('{}.{}').format(out, ext)):
            index += 1
            out = os.path.join(cwd, six.u('{}_{}').format(name, index))
        return six.u('{}.{}').format(out, ext)

    # fetch the job again in case the database connection was lost during the job or something else changed.
    job = WooeyJob.objects.get(pk=job_id)
    # if there are files generated, make zip/tar files for download
    if len(os.listdir(abscwd)):
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
                try:
                    zip.write(path, arcname=os.path.join(arcname, filename))
                except:
                    stderr = '{}\n{}'.format(stderr, traceback.format_exc())
        try:
            zip.close()
        except:
            stderr = '{}\n{}'.format(stderr, traceback.format_exc())

        # save all the files generated as well to our default storage for ephemeral storage setups
        if wooey_settings.WOOEY_EPHEMERAL_FILES:
            for root, folders, files in os.walk(abscwd):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    s3path = os.path.join(root[root.find(cwd):], filename)
                    remote = utils.get_storage(local=False)
                    exists = remote.exists(s3path)
                    filesize = remote.size(s3path) if exists else 0
                    if not exists or (exists and filesize == 0):
                        if exists:
                            remote.delete(s3path)
                        remote.save(s3path, File(open(filepath, 'rb')))
    utils.create_job_fileinfo(job)

    job.stdout = stdout
    job.stderr = stderr
    job.status = WooeyJob.COMPLETED
    job.save()

    return (stdout, stderr)
