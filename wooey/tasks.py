from __future__ import absolute_import
import os
import subprocess
import sys
import tarfile
import tempfile
import traceback
import zipfile
from datetime import timedelta
from threading import Thread

from django.utils.text import get_valid_filename
from django.core.files import File
from django.conf import settings
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from celery import app
from celery.schedules import crontab
from celery.signals import worker_process_init

from .backend import utils
from . import settings as wooey_settings

try:
    from Queue import Empty, Queue
except ImportError:
    from queue import Empty, Queue  # python 3.x

ON_POSIX = "posix" in sys.builtin_module_names

celery_app = app.app_or_default()


def revoke_job_task(task_id):
    if task_id:
        celery_app.control.revoke(task_id)


def queue_script_job(
    job_id, rerun=False, increment_retry_count=False, revoke_existing=False
):
    from .models import WooeyJob

    job = WooeyJob.objects.get(pk=job_id)
    if revoke_existing:
        revoke_job_task(job.celery_id)
        WooeyJob.objects.filter(pk=job_id).update(celery_id=None)

    async_result = submit_script.delay(wooey_job=job_id, rerun=rerun)
    update_kwargs = {
        "celery_id": async_result.id,
        "status": WooeyJob.QUEUED,
    }
    if increment_retry_count:
        update_kwargs["retry_count"] = F("retry_count") + 1
    WooeyJob.objects.filter(pk=job_id).update(**update_kwargs)
    return async_result


def enqueue_output(out, q):
    for line in iter(out.readline, b""):
        q.put(line.decode("utf-8"))
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

    out += "".join(map(str, lines))
    return out


@worker_process_init.connect
def configure_workers(*args, **kwargs):
    # this sets up Django on nodes started by the worker daemon.
    import django

    django.setup()


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


def run_and_stream_command(command, cwd=None, job=None, stdout="", stderr=""):
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        bufsize=0,
    )

    # We need to use subprocesses to capture the IO, otherwise they will block one another
    # i.e. a check against stderr will sit waiting on stderr before returning
    # we use Queues to communicate
    qout, qerr = Queue(), Queue()
    pout = output_monitor_queue(qout, proc.stdout)
    perr = output_monitor_queue(qerr, proc.stderr)

    prev_std = (stdout, stderr)

    def check_output(job, stdout, stderr, prev_std):
        # Check for updates from either (non-blocking)
        stdout = update_from_output_queue(qout, stdout)
        stderr = update_from_output_queue(qerr, stderr)

        # If there are changes, update the db
        if job is not None and (stdout, stderr) != prev_std:
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
    return_code = proc.returncode
    return (stdout, stderr, return_code)


def setup_venv(virtual_environment, job=None, stdout="", stderr=""):
    venv_path = virtual_environment.get_install_path()
    venv_executable = virtual_environment.get_venv_python_binary()
    return_code = 0

    if not os.path.exists(venv_path):
        stdout += _("Setting up Virtual Environment\n########\n")
        venv_command = [
            virtual_environment.python_binary,
            "-m",
            "venv",
            venv_path,
            "--without-pip",
            "--system-site-packages",
        ]
        stdout, stderr, return_code = run_and_stream_command(
            venv_command, cwd=None, job=job, stdout=stdout, stderr=stderr
        )

        if return_code:
            raise Exception(
                _("VirtualEnv setup failed.\n{stdout}\n{stderr}").format(
                    stdout=stdout, stderr=stderr
                )
            )
        pip_setup = [venv_executable, "-m", "pip", "install", "-I", "pip"]
        stdout += _("Installing Pip\n########\n")
        stdout, stderr, return_code = run_and_stream_command(
            pip_setup, cwd=None, job=job, stdout=stdout, stderr=stderr
        )
        if return_code:
            raise Exception(
                _("Pip setup failed.\n{stdout}\n{stderr}").format(
                    stdout=stdout, stderr=stderr
                )
            )
    requirements = virtual_environment.requirements
    if requirements:
        with tempfile.NamedTemporaryFile(
            mode="w", prefix="requirements", suffix=".txt", delete=False
        ) as reqs_txt:
            reqs_txt.write(requirements)
        venv_command = [
            venv_executable,
            "-m",
            "pip",
            "install",
            "-r",
            reqs_txt.name,
        ]
        stdout += _("Installing Requirements\n########\n")
        stdout, stderr, return_code = run_and_stream_command(
            venv_command, cwd=None, job=job, stdout=stdout, stderr=stderr
        )
        if return_code:
            raise Exception(
                _("Requirements setup failed.\n{stdout}\n{stderr}").format(
                    stdout=stdout, stderr=stderr
                )
            )
        os.remove(reqs_txt.name)
    stdout += _("Virtual Environment Setup Complete\n########\n")
    return (venv_executable, stdout, stderr, return_code)


@celery_app.task()
def submit_script(**kwargs):
    job_id = kwargs.pop("wooey_job")
    resubmit = kwargs.pop("wooey_resubmit", False)
    from .models import WooeyJob

    job = WooeyJob.objects.get(pk=job_id)
    job.update_realtime(delete=True)
    stdout, stderr = "", ""

    try:
        virtual_environment = job.script_version.script.virtual_environment
        if virtual_environment:
            venv_executable, stdout, stderr, return_code = setup_venv(
                virtual_environment, job, stdout, stderr
            )
            if return_code:
                raise Exception(
                    "Virtual env setup failed.\n{}\n{}".format(stdout, stderr)
                )
        else:
            venv_executable = None

        command = utils.get_job_commands(job=job, executable=venv_executable)
        if resubmit:
            # clone ourselves, setting pk=None seems hackish but it works
            job.pk = None

        # This is where the script works from -- it is what is after the media_root since that may change between
        # setups/where our user uploads are stored.
        cwd = job.get_output_path()

        abscwd = os.path.abspath(os.path.join(settings.MEDIA_ROOT, cwd))
        job.command = " ".join(command)
        job.save_path = cwd

        utils.mkdirs(abscwd)
        # make sure we have the script, otherwise download it. This can happen if we have an ephemeral file system or are
        # executing jobs on a worker node.
        get_latest_script(job.script_version)

        job.status = WooeyJob.RUNNING
        job.save()

        stdout, stderr, return_code = run_and_stream_command(
            command, abscwd, job, stdout, stderr
        )

        # fetch the job again in case the database connection was lost during the job or something else changed.
        job = WooeyJob.objects.get(pk=job_id)
        # if there are files generated, make zip/tar files for download
        if len(os.listdir(abscwd)):
            tar_out = utils.get_available_file(
                abscwd, get_valid_filename(job.job_name), "tar.gz"
            )
            tar = tarfile.open(tar_out, "w:gz")
            tar_name = os.path.splitext(os.path.splitext(os.path.split(tar_out)[1])[0])[
                0
            ]
            tar.add(abscwd, arcname=tar_name)
            tar.close()

            zip_out = utils.get_available_file(
                abscwd, get_valid_filename(job.job_name), "zip"
            )
            zip = zipfile.ZipFile(zip_out, "w")
            arcname = os.path.splitext(os.path.split(zip_out)[1])[0]
            zip.write(abscwd, arcname=arcname)
            base_dir = os.path.split(zip_out)[0]
            for root, folders, filenames in os.walk(base_dir):
                for filename in filenames:
                    path = os.path.join(root, filename)
                    archive_name = path.replace(base_dir, "")
                    if archive_name.startswith(os.path.sep):
                        archive_name = archive_name.replace(os.path.sep, "", 1)
                    archive_name = os.path.join(arcname, archive_name)
                    if path == tar_out:
                        continue
                    if path == zip_out:
                        continue
                    try:
                        zip.write(path, arcname=archive_name)
                    except Exception:
                        stderr += "{}\n{}".format(stderr, traceback.format_exc())
            try:
                zip.close()
            except Exception:
                stderr += "{}\n{}".format(stderr, traceback.format_exc())

            # save all the files generated as well to our default storage for ephemeral storage setups
            if wooey_settings.WOOEY_EPHEMERAL_FILES:
                for root, folders, files in os.walk(abscwd):
                    for filename in files:
                        filepath = os.path.join(root, filename)
                        s3path = os.path.join(root[root.find(cwd) :], filename)
                        remote = utils.get_storage(local=False)
                        exists = remote.exists(s3path)
                        filesize = remote.size(s3path) if exists else 0
                        if not exists or (exists and filesize == 0):
                            if exists:
                                remote.delete(s3path)
                            remote.save(s3path, File(open(filepath, "rb")))
        utils.create_job_fileinfo(job)
        job.status = WooeyJob.COMPLETED if return_code == 0 else WooeyJob.FAILED
        job.update_realtime(delete=True)
    except Exception:
        stderr += "{}\n{}".format(stderr, traceback.format_exc())
        job.status = WooeyJob.ERROR
    job.stdout = stdout
    job.stderr = stderr
    job.save()

    return (stdout, stderr)


@celery_app.task()
def cleanup_wooey_jobs(**kwargs):
    from django.utils import timezone
    from .models import WooeyJob

    cleanup_settings = wooey_settings.WOOEY_JOB_EXPIRATION
    anon_settings = cleanup_settings.get("anonymous")
    now = timezone.now()
    if anon_settings:
        WooeyJob.objects.filter(
            user=None, created_date__lte=now - anon_settings
        ).delete()
    user_settings = cleanup_settings.get("user")
    if user_settings:
        WooeyJob.objects.filter(
            user__isnull=False, created_date__lte=now - user_settings
        ).delete()


@celery_app.task()
def cleanup_dead_jobs():
    return cleanup_stuck_jobs()


def _extract_task_ids(worker_info):
    task_ids = set()
    if not worker_info:
        return task_ids

    for tasks in worker_info.values():
        for task in tasks or []:
            request = task.get("request")
            if isinstance(request, dict) and request.get("id"):
                task_ids.add(request["id"])
                continue

            if task.get("id"):
                task_ids.add(task["id"])

    return task_ids


@celery_app.task()
def cleanup_stuck_jobs():
    """
    This cleans up jobs that are stuck in limbo between Wooey and the task broker.
    """
    from django.utils import timezone
    from .models import WooeyJob

    inspect = celery_app.control.inspect()
    active_info = inspect.active()
    reserved_info = inspect.reserved()
    scheduled_info = inspect.scheduled()

    # If we cannot connect to the workers, we do not know if the tasks are running or queued.
    if all(info is None for info in (active_info, reserved_info, scheduled_info)):
        return

    now = timezone.now()
    minimum_cleanup_age = timedelta(minutes=10)
    oldest_cleanup_eligible = now - minimum_cleanup_age
    active_task_ids = _extract_task_ids(active_info)
    queued_task_ids = (
        active_task_ids
        | _extract_task_ids(reserved_info)
        | _extract_task_ids(scheduled_info)
    )

    queue_timeout = (
        wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT
        if wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT is not None
        else timedelta(hours=24)
    )
    resubmit_timeout = (
        wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT
        if wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT is not None
        else timedelta(hours=1)
    )
    resubmit_limit = (
        wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT
        if wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT is not None
        else 0
    )

    active_jobs = WooeyJob.objects.filter(
        status=WooeyJob.RUNNING,
        created_date__lte=oldest_cleanup_eligible,
    )
    to_disable = set()
    for job in active_jobs:
        if job.celery_id not in active_task_ids:
            to_disable.add(job.pk)

    queued_jobs = WooeyJob.objects.filter(
        status__in=(WooeyJob.SUBMITTED, WooeyJob.RETRY, WooeyJob.QUEUED),
        created_date__lte=oldest_cleanup_eligible,
    )
    jobs_to_resubmit = []
    jobs_to_mark_queued = set()
    task_ids_to_revoke = set()
    for job in queued_jobs:
        if job.celery_id in active_task_ids:
            continue

        if job.created_date <= now - queue_timeout:
            task_ids_to_revoke.add(job.celery_id)
            to_disable.add(job.pk)
            continue

        if job.celery_id in queued_task_ids:
            if job.status in (WooeyJob.SUBMITTED, WooeyJob.RETRY):
                jobs_to_mark_queued.add(job.pk)
            continue

        if job.status == WooeyJob.QUEUED:
            continue

        if job.modified_date > now - resubmit_timeout:
            continue

        if job.retry_count >= resubmit_limit:
            task_ids_to_revoke.add(job.celery_id)
            to_disable.add(job.pk)
            continue

        jobs_to_resubmit.append(job.pk)

    for task_id in task_ids_to_revoke:
        revoke_job_task(task_id)

    WooeyJob.objects.filter(pk__in=jobs_to_mark_queued).update(status=WooeyJob.QUEUED)
    WooeyJob.objects.filter(pk__in=to_disable).update(status=WooeyJob.FAILED)

    for job_id in jobs_to_resubmit:
        WooeyJob.objects.filter(pk=job_id).update(status=WooeyJob.RETRY)
        queue_script_job(
            job_id,
            rerun=False,
            increment_retry_count=True,
            revoke_existing=True,
        )


celery_app.conf.beat_schedule.update(
    {
        "cleanup-old-jobs": {
            "task": "wooey.tasks.cleanup_wooey_jobs",
            "schedule": crontab(hour=0, minute=0),  # cleanup at midnight each day
        },
        "cleanup-stuck-jobs": {
            "task": "wooey.tasks.cleanup_stuck_jobs",
            "schedule": crontab(minute="*/10"),  # run every 10 minutes
        },
    }
)
