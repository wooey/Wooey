from __future__ import absolute_import
import os
import subprocess
import sys
import tarfile
import tempfile
import traceback
import zipfile
from threading import Thread

import six
from django.utils.text import get_valid_filename
from django.core.files import File
from django.conf import settings

from celery import Task
from celery import app
from celery.schedules import crontab
from celery.signals import worker_process_init

from .backend import utils
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


def get_latest_script(script_version):
    """Downloads the latest script version to the local storage.

    :param script_version: :py:class:`~wooey.models.core.ScriptVersion`
    :return: boolean
        Returns true if a new version was downloaded.
    """
    script_path = script_version.script_path
    local_storage = utils.get_storage(local=True)
    script_exists = local_storage.exists(script_path.name)
    if not script_exists:
        local_storage.save(script_path.name, script_path.file)
        return True
    else:
        # If script exists, make sure the version is valid, otherwise fetch a new one
        script_contents = local_storage.open(script_path.name).read()
        script_checksum = utils.get_checksum(buff=script_contents)
        if script_checksum != script_version.checksum:
            tf = tempfile.TemporaryFile()
            with tf:
                tf.write(script_contents)
                tf.seek(0)
                local_storage.delete(script_path.name)
                local_storage.save(script_path.name, tf)
                return True
    return False


@celery_app.task(base=WooeyTask)
def submit_script(**kwargs):
    job_id = kwargs.pop('wooey_job')
    resubmit = kwargs.pop('wooey_resubmit', False)
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
    get_latest_script(job.script_version)


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
        base_dir = os.path.split(zip_out)[0]
        for root, folders, filenames in os.walk(base_dir):
            for filename in filenames:
                path = os.path.join(root, filename)
                archive_name = path.replace(base_dir, '')
                if archive_name.startswith(os.path.sep):
                    archive_name = archive_name.replace(os.path.sep, '', 1)
                archive_name = os.path.join(arcname, archive_name)
                if path == tar_out:
                    continue
                if path == zip_out:
                    continue
                try:
                    zip.write(path, arcname=archive_name)
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


@celery_app.task(base=WooeyTask)
def cleanup_dead_jobs():
    """
    This cleans up jobs that have been marked as ran, but are not queue'd in celery. It is meant
    to cleanup jobs that have been lost due to a server crash or some other reason a job is
    in limbo.
    """
    from .models import WooeyJob

    # Get active tasks from Celery
    inspect = celery_app.control.inspect()
    worker_info = inspect.active()

    # If we cannot connect to the workers, we do not know if the tasks are running or not, so
    # we cannot mark them as dead
    if not worker_info:
        return

    active_tasks = {task['id'] for worker, tasks in six.iteritems(worker_info) for task in tasks}

    # find jobs that are marked as running but not present in celery's active tasks
    active_jobs = WooeyJob.objects.filter(status=WooeyJob.RUNNING)
    to_disable = set()
    for job in active_jobs:
        if job.celery_id not in active_tasks:
            to_disable.add(job.pk)

    WooeyJob.objects.filter(pk__in=to_disable).update(status=WooeyJob.FAILED)


celery_app.conf.beat_schedule.update({
    'cleanup-old-jobs': {
        'task': 'wooey.tasks.cleanup_wooey_jobs',
        'schedule': crontab(hour=0, minute=0),  # cleanup at midnight each day
    },
    'cleanup-dead-jobs': {
        'task': 'wooey.tasks.cleanup_dead_jobs',
        'schedule': crontab(minute='*/10'),  # run every 6 minutes
    }
})
