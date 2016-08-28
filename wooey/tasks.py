from __future__ import absolute_import
import subprocess
import tarfile
import os
import zipfile
import six
import sys
import traceback

from threading import Thread

from django.utils.text import get_valid_filename
from django.core.files import File
from django.conf import settings

from celery import Task
from celery import app
from celery.schedules import crontab
from celery.signals import worker_process_init

from . import settings as wooey_settings

try:
    from Queue import Empty, Queue
except ImportError:
    from queue import Empty, Queue  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names

celery_app = app.app_or_default()


def enqueue_output(out, q):
    for line in iter(out.readline, b''):
        q.put(line.decode('utf-8'))
    try:
        out.close()
    except IOError:
        pass


def output_monitor_queue(queue, out):
    p = Thread(target=enqueue_output, args=(out, queue))
    p.start()
    return p


def update_from_output_queue(queue, out):
    lines = []
    while True:
        try:
            line = queue.get_nowait()
            lines.append(line)
        except Empty:
            break

    out += ''.join(map(str, lines))
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
    from .models import WooeyJob, UserFile
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
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=abscwd, bufsize=0)

    # We need to use subprocesses to capture the IO, otherwise they will block one another
    # i.e. a check against stderr will sit waiting on stderr before returning
    # we use Queues to communicate
    qout, qerr = Queue(), Queue()
    pout = output_monitor_queue(qout, proc.stdout)
    perr = output_monitor_queue(qerr, proc.stderr)

    prev_std = None

    def check_output(job, stdout, stderr, prev_std):
        # Check for updates from either (non-blocking)
        stdout = update_from_output_queue(qout, stdout)
        stderr = update_from_output_queue(qerr, stderr)

        # If there are changes, update the db
        if (stdout, stderr) != prev_std:
            job.update_realtime(stdout=stdout, stderr=stderr)
            prev_std = (stdout, stderr)

        return stdout, stderr, prev_std

    # Loop until the process is complete + both stdout/stderr have EOFd
    while proc.poll() is None or pout.is_alive() or perr.is_alive():
        stdout, stderr, prev_std = check_output(job, stdout, stderr, prev_std)

    # Catch any remaining output
    try:
        proc.stdout.flush()
    except ValueError:  # Handle if stdout is closed
        pass
    stdout, stderr, prev_std = check_output(job, stdout, stderr, prev_std)

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
    job.update_realtime(delete=True)
    job.save()

    return (stdout, stderr)


@celery_app.task(base=WooeyTask)
def cleanup_wooey_jobs(**kwargs):
    from django.utils import timezone
    from .models import WooeyJob

    cleanup_settings = wooey_settings.WOOEY_JOB_EXPIRATION
    anon_settings = cleanup_settings.get('anonymous')
    now = timezone.now()
    if anon_settings:
        WooeyJob.objects.filter(user=None, created_date__lte=now-anon_settings).delete()
    user_settings = cleanup_settings.get('user')
    if user_settings:
        WooeyJob.objects.filter(user__isnull=False, created_date__lte=now-user_settings).delete()


celery_app.conf.update(
    CELERYBEAT_SCHEDULE={
        'cleanup-old-jobs': {
            'task': 'wooey.tasks.cleanup_wooey_jobs',
            'schedule': crontab(hour=0, minute=0),  # cleanup at midnight each day
        },
    }
)
