from __future__ import absolute_import
import subprocess
import tarfile
import os
import zipfile
import six
import sys
import traceback

from django.utils.text import get_valid_filename
from django.core.files import File
from django.conf import settings

from celery import Task
from celery import app
from celery.signals import worker_process_init

from . import settings as wooey_settings

from billiard import Process, Queue
try:
    from Queue import Empty
except ImportError:
    from queue import Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names

celery_app = app.app_or_default()


def enqueue_output(out, q):
    for line in iter(out.readline, b''):
        q.put(line)
    out.close()


def output_monitor_queue(out):
    q = Queue()
    p = Process(target=enqueue_output, args=(out, q))
    p.start()
    return q, p


def update_from_output_queue(q, out):
    try:
        line = q.get_nowait()
    except Empty:
        return out

    out += str(line)
    return out



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

    stdout, stderr = '', ''
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=abscwd)

    # We need to use subprocesses to capture the IO, otherwise they will block one another
    # i.e. a check against stderr will sit waiting on stderr before returning
    # we use Queues to communicate
    qout, pout = output_monitor_queue(proc.stdout)
    qerr, perr = output_monitor_queue(proc.stderr)

    prev_std = None

    # Loop until the process is complete + both stdout/stderr have EOFd
    while proc.poll() is None or pout.is_alive() or perr.is_alive():

        # Check for updates from either (non-blocking)
        stdout = update_from_output_queue(qout, stdout)
        stderr = update_from_output_queue(qerr, stderr)

        # If there are changes, update the db
        if (stdout, stderr) != prev_std:
            job.stdout = stdout
            job.stderr = stderr
            job.save()

            prev_std = (stdout, stderr)

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
