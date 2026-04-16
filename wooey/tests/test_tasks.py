import mock
import os
from datetime import timedelta

from django.test import TestCase

from wooey import settings as wooey_settings
from wooey.backend.utils import add_wooey_script
from wooey.models import (
    WooeyJob,
)
from wooey.tasks import (
    cleanup_stuck_jobs,
    get_latest_script,
)

from . import config, mixins, factories


class TaskTests(mixins.ScriptFactoryMixin, TestCase):
    def test_job_cleanup(self):
        from ..models import WooeyJob
        from ..tasks import cleanup_wooey_jobs
        import time

        anon_job = factories.generate_job(self.translate_script)
        user_job = factories.generate_job(self.translate_script)
        user = factories.UserFactory()
        user_job.user = user
        user_job.save()
        wooey_settings.WOOEY_JOB_EXPIRATION.update(
            {
                "user": timedelta(hours=1),
                "anonymous": timedelta(hours=1),
            }
        )
        cleanup_wooey_jobs()
        self.assertListEqual(list(WooeyJob.objects.all()), [anon_job, user_job])
        time.sleep(0.1)
        wooey_settings.WOOEY_JOB_EXPIRATION.update(
            {
                "user": timedelta(hours=1),
                "anonymous": timedelta(microseconds=1),
            }
        )
        cleanup_wooey_jobs()
        self.assertListEqual(list(WooeyJob.objects.all()), [user_job])

        wooey_settings.WOOEY_JOB_EXPIRATION.update(
            {
                "user": timedelta(microseconds=1),
                "anonymous": timedelta(microseconds=1),
            }
        )

        cleanup_wooey_jobs()
        self.assertListEqual(list(WooeyJob.objects.all()), [])


class TestGetLatestScript(mixins.FileMixin, mixins.ScriptTearDown, TestCase):
    def setUp(self):
        super(TestGetLatestScript, self).setUp()
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, "versioned_script", "v1.py")
        with open(script) as o:
            v1 = self.storage.save(self.filename_func("v1.py"), o)
        res = add_wooey_script(script_path=v1, script_name="test_versions")
        self.first_version = self.rename_script(res["script"])

    def rename_script(self, script_version):
        # Because we are on local storage, the script uploaded will already be present, so
        # we rename it to mimic it being absent on a worker node
        new_name = self.storage.save(
            script_version.script_path.name, script_version.script_path.file
        )
        script_version.script_path.name = new_name
        script_version.save()
        return script_version

    def test_get_latest_script_loads_initial(self):
        self.assertTrue(get_latest_script(self.first_version))

    def test_get_latest_script_doesnt_redownload_same_script(self):
        self.assertTrue(get_latest_script(self.first_version))
        self.assertFalse(get_latest_script(self.first_version))

    def test_get_latest_script_downloads_new_script(self):
        get_latest_script(self.first_version)

        # Update the script version
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, "versioned_script", "v2.py")
        with open(script) as o:
            v2 = self.storage.save(self.filename_func("v2.py"), o)

        res = add_wooey_script(script_path=v2, script_name="test_versions")
        second_version = self.rename_script(res["script"])

        self.assertTrue(get_latest_script(second_version))


class TestCleanupStuckJobs(mixins.ScriptFactoryMixin, TestCase):
    def setUp(self):
        super(TestCleanupStuckJobs, self).setUp()
        self.queue_timeout = wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT
        self.resubmit_timeout = wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT
        self.resubmit_limit = wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT
        self.addCleanup(self.restore_job_settings)

    def restore_job_settings(self):
        wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT = self.queue_timeout
        wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT = self.resubmit_timeout
        wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT = self.resubmit_limit

    def test_handles_unresponsive_workers(self):
        # Ensure that if we cannot connect to celery, we do nothing.
        with mock.patch("wooey.tasks.celery_app.control.inspect") as inspect_mock:
            running_job = factories.generate_job(self.translate_script)
            running_job.status = WooeyJob.RUNNING
            running_job.save()

            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(
                    return_value=None,
                ),
                reserved=mock.Mock(return_value=None),
                scheduled=mock.Mock(return_value=None),
            )
            cleanup_stuck_jobs()
            self.assertEqual(
                WooeyJob.objects.get(pk=running_job.id).status, WooeyJob.RUNNING
            )

    def test_cleans_up_dead_running_jobs(self):
        from django.utils import timezone

        # Make a job that is running but not active, and a job that is running and active.
        dead_job = factories.generate_job(self.translate_script)
        dead_job.status = WooeyJob.RUNNING
        dead_job.save()
        active_job = factories.generate_job(self.translate_script)
        active_job.status = WooeyJob.RUNNING
        active_job.celery_id = "celery-id"
        active_job.save()
        WooeyJob.objects.filter(pk__in=(dead_job.pk, active_job.pk)).update(
            created_date=timezone.now() - timedelta(minutes=15),
            modified_date=timezone.now() - timedelta(minutes=15),
        )
        with mock.patch("wooey.tasks.celery_app.control.inspect") as inspect_mock:
            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(
                    return_value={
                        "worker-id": [
                            {
                                "id": active_job.celery_id,
                            }
                        ]
                    },
                )
            )
            inspect_mock.return_value.reserved = mock.Mock(return_value={})
            inspect_mock.return_value.scheduled = mock.Mock(return_value={})
            cleanup_stuck_jobs()

            # Assert the dead job is updated
            self.assertEqual(
                WooeyJob.objects.get(pk=dead_job.id).status, WooeyJob.FAILED
            )
            self.assertEqual(
                WooeyJob.objects.get(pk=active_job.id).status, WooeyJob.RUNNING
            )

    def test_marks_visible_waiting_jobs_as_queued(self):
        from django.utils import timezone

        waiting_job = factories.generate_job(self.translate_script)
        waiting_job.celery_id = "queued-task-id"
        waiting_job.save()
        WooeyJob.objects.filter(pk=waiting_job.pk).update(
            created_date=timezone.now() - timedelta(minutes=15),
            modified_date=timezone.now() - timedelta(minutes=15),
        )

        with mock.patch("wooey.tasks.celery_app.control.inspect") as inspect_mock:
            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(return_value={}),
                reserved=mock.Mock(
                    return_value={"worker-id": [{"id": waiting_job.celery_id}]}
                ),
                scheduled=mock.Mock(return_value={}),
            )
            cleanup_stuck_jobs()

        self.assertEqual(
            WooeyJob.objects.get(pk=waiting_job.pk).status, WooeyJob.QUEUED
        )

    def test_ignores_jobs_younger_than_minimum_cleanup_age(self):
        from django.utils import timezone

        fresh_running_job = factories.generate_job(self.translate_script)
        fresh_running_job.status = WooeyJob.RUNNING
        fresh_running_job.save()
        fresh_waiting_job = factories.generate_job(self.translate_script)
        fresh_waiting_job.status = WooeyJob.RETRY
        fresh_waiting_job.celery_id = "fresh-task-id"
        fresh_waiting_job.save()
        WooeyJob.objects.filter(
            pk__in=(fresh_running_job.pk, fresh_waiting_job.pk)
        ).update(
            created_date=timezone.now() - timedelta(minutes=5),
            modified_date=timezone.now() - timedelta(hours=2),
        )

        with mock.patch("wooey.tasks.celery_app.control.inspect") as inspect_mock:
            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(return_value={}),
                reserved=mock.Mock(return_value={}),
                scheduled=mock.Mock(return_value={}),
            )
            with mock.patch("wooey.tasks.celery_app.control.revoke") as revoke_mock:
                with mock.patch("wooey.tasks.submit_script.delay") as delay_mock:
                    cleanup_stuck_jobs()
                    self.assertFalse(revoke_mock.called)
                    self.assertFalse(delay_mock.called)

        fresh_running_job.refresh_from_db()
        fresh_waiting_job.refresh_from_db()
        self.assertEqual(fresh_running_job.status, WooeyJob.RUNNING)
        self.assertEqual(fresh_waiting_job.status, WooeyJob.RETRY)

    def test_requeues_stale_waiting_jobs_and_revokes_old_task(self):
        from django.utils import timezone

        retry_job = factories.generate_job(self.translate_script)
        retry_job.status = WooeyJob.RETRY
        retry_job.celery_id = "stale-task-id"
        retry_job.retry_count = 1
        retry_job.save()
        WooeyJob.objects.filter(pk=retry_job.pk).update(
            created_date=timezone.now() - timedelta(hours=2),
            modified_date=timezone.now() - timedelta(hours=2),
        )

        wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT = timedelta(hours=24)
        wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT = timedelta(hours=1)
        wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT = 3

        with mock.patch("wooey.tasks.celery_app.control.inspect") as inspect_mock:
            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(return_value={}),
                reserved=mock.Mock(return_value={}),
                scheduled=mock.Mock(return_value={}),
            )
            with mock.patch("wooey.tasks.celery_app.control.revoke") as revoke_mock:
                with mock.patch("wooey.tasks.submit_script.delay") as delay_mock:
                    delay_mock.return_value = mock.Mock(id="resubmitted-task-id")
                    cleanup_stuck_jobs()
                    revoke_mock.assert_called_once_with("stale-task-id")
                    delay_mock.assert_called_once_with(
                        wooey_job=retry_job.pk, rerun=False
                    )

        retry_job.refresh_from_db()
        self.assertEqual(retry_job.status, WooeyJob.QUEUED)
        self.assertEqual(retry_job.retry_count, 2)
        self.assertEqual(retry_job.celery_id, "resubmitted-task-id")

    def test_does_not_requeue_jobs_already_queued_on_broker(self):
        from django.utils import timezone

        queued_job = factories.generate_job(self.translate_script)
        queued_job.status = WooeyJob.QUEUED
        queued_job.celery_id = "queued-task-id"
        queued_job.save()
        WooeyJob.objects.filter(pk=queued_job.pk).update(
            created_date=timezone.now() - timedelta(hours=2),
            modified_date=timezone.now() - timedelta(hours=2),
        )

        wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT = timedelta(hours=24)
        wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT = timedelta(hours=1)
        wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT = 3

        with mock.patch("wooey.tasks.celery_app.control.inspect") as inspect_mock:
            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(return_value={}),
                reserved=mock.Mock(return_value={}),
                scheduled=mock.Mock(return_value={}),
            )
            with mock.patch("wooey.tasks.celery_app.control.revoke") as revoke_mock:
                with mock.patch("wooey.tasks.submit_script.delay") as delay_mock:
                    cleanup_stuck_jobs()
                    self.assertFalse(revoke_mock.called)
                    self.assertFalse(delay_mock.called)

        self.assertEqual(WooeyJob.objects.get(pk=queued_job.pk).status, WooeyJob.QUEUED)

    def test_fails_queued_jobs_that_exceed_queue_timeout(self):
        from django.utils import timezone

        queued_job = factories.generate_job(self.translate_script)
        queued_job.status = WooeyJob.QUEUED
        queued_job.celery_id = "queued-task-id"
        queued_job.save()
        WooeyJob.objects.filter(pk=queued_job.pk).update(
            created_date=timezone.now() - timedelta(hours=25),
            modified_date=timezone.now() - timedelta(hours=2),
        )

        wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT = timedelta(hours=24)
        wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT = timedelta(hours=1)
        wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT = 3

        with mock.patch("wooey.tasks.celery_app.control.inspect") as inspect_mock:
            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(return_value={}),
                reserved=mock.Mock(return_value={}),
                scheduled=mock.Mock(return_value={}),
            )
            with mock.patch("wooey.tasks.celery_app.control.revoke") as revoke_mock:
                with mock.patch("wooey.tasks.submit_script.delay") as delay_mock:
                    cleanup_stuck_jobs()
                    revoke_mock.assert_called_once_with("queued-task-id")
                    self.assertFalse(delay_mock.called)

        self.assertEqual(WooeyJob.objects.get(pk=queued_job.pk).status, WooeyJob.FAILED)

    def test_fails_waiting_jobs_that_hit_retry_limit(self):
        from django.utils import timezone

        retry_job = factories.generate_job(self.translate_script)
        retry_job.status = WooeyJob.RETRY
        retry_job.celery_id = "stale-task-id"
        retry_job.retry_count = 3
        retry_job.save()
        WooeyJob.objects.filter(pk=retry_job.pk).update(
            created_date=timezone.now() - timedelta(hours=2),
            modified_date=timezone.now() - timedelta(hours=2),
        )

        wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT = timedelta(hours=24)
        wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT = timedelta(hours=1)
        wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT = 3

        with mock.patch("wooey.tasks.celery_app.control.inspect") as inspect_mock:
            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(return_value={}),
                reserved=mock.Mock(return_value={}),
                scheduled=mock.Mock(return_value={}),
            )
            with mock.patch("wooey.tasks.celery_app.control.revoke") as revoke_mock:
                with mock.patch("wooey.tasks.submit_script.delay") as delay_mock:
                    cleanup_stuck_jobs()
                    revoke_mock.assert_called_once_with("stale-task-id")
                    self.assertFalse(delay_mock.called)

        retry_job.refresh_from_db()
        self.assertEqual(retry_job.status, WooeyJob.FAILED)
