import mock
import os
import uuid
from datetime import timedelta

from django.db import transaction
from django.test import TestCase

from wooey import settings as wooey_settings
from wooey.backend.utils import add_wooey_script
from wooey.models import (
    WooeyJob,
)
from wooey.tasks import (
    cleanup_stuck_jobs,
    get_latest_script,
    queue_script_job,
    submit_script,
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


class TestQueueScriptJob(mixins.ScriptFactoryMixin, TestCase):
    def test_stale_submission_does_not_execute_script(self):
        job = factories.generate_job(self.translate_script)

        with mock.patch("wooey.tasks.submit_script.apply_async") as apply_async_mock:
            with self.captureOnCommitCallbacks(execute=True):
                queue_script_job(job.pk)

        job.refresh_from_db()
        old_submission_id = job.submission_id
        worker_kwargs = dict(apply_async_mock.call_args.kwargs["kwargs"])
        dispatched_submission_id = worker_kwargs.get("submission_id")
        worker_kwargs.setdefault("submission_id", str(old_submission_id))

        new_submission_id = uuid.uuid4()
        WooeyJob.objects.filter(pk=job.pk).update(
            status=WooeyJob.QUEUED,
            submission_id=new_submission_id,
            celery_id="new-task-id",
        )

        with (
            mock.patch.object(WooeyJob, "update_realtime") as update_realtime_mock,
            mock.patch(
                "wooey.tasks.utils.get_job_commands",
                side_effect=RuntimeError("stale task reached script setup"),
            ),
        ):
            submit_script(**worker_kwargs)

        update_realtime_mock.assert_not_called()
        self.assertEqual(str(dispatched_submission_id), str(old_submission_id))
        job.refresh_from_db()
        self.assertEqual(job.status, WooeyJob.QUEUED)
        self.assertEqual(job.submission_id, new_submission_id)
        self.assertEqual(job.celery_id, "new-task-id")

    def test_rollback_discards_pending_publish(self):
        job = factories.generate_job(self.translate_script)

        with mock.patch("wooey.tasks.submit_script.apply_async") as apply_async_mock:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                with self.assertRaisesRegex(RuntimeError, "roll back"):
                    with transaction.atomic():
                        queue_script_job(job.pk)
                        raise RuntimeError("roll back")

            self.assertEqual(callbacks, [])
            apply_async_mock.assert_not_called()

        job.refresh_from_db()
        self.assertIsNone(job.celery_id)
        self.assertIsNone(job.submission_id)

    def test_records_task_id_before_publishing_after_commit(self):
        job = factories.generate_job(self.translate_script)

        with mock.patch("wooey.tasks.submit_script.apply_async") as apply_async_mock:
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                celery_id = queue_script_job(job.pk)
                job.refresh_from_db()
                self.assertEqual(job.celery_id, celery_id)
                self.assertEqual(job.status, WooeyJob.SUBMITTED)
                apply_async_mock.assert_not_called()

            self.assertEqual(len(callbacks), 1)
            callbacks[0]()

            apply_async_mock.assert_called_once_with(
                kwargs={
                    "wooey_job": job.pk,
                    "rerun": False,
                    "submission_id": str(job.submission_id),
                },
                task_id=celery_id,
            )
        job.refresh_from_db()
        self.assertEqual(job.status, WooeyJob.QUEUED)

    def test_failed_dispatch_remains_waiting_for_resubmission(self):
        job = factories.generate_job(self.translate_script)

        with mock.patch(
            "wooey.tasks.submit_script.apply_async",
            side_effect=RuntimeError("broker unavailable"),
        ):
            with self.assertRaisesRegex(RuntimeError, "broker unavailable"):
                with self.captureOnCommitCallbacks(execute=True):
                    queue_script_job(job.pk)

        job.refresh_from_db()
        self.assertEqual(job.status, WooeyJob.SUBMITTED)
        self.assertIsNotNone(job.celery_id)
        self.assertIsNotNone(job.submission_id)

    def test_preserves_state_set_by_task_during_dispatch(self):
        job = factories.generate_job(self.translate_script)

        def complete_job_immediately(*, kwargs, task_id):
            WooeyJob.objects.filter(pk=kwargs["wooey_job"]).update(
                status=WooeyJob.COMPLETED
            )

        with mock.patch(
            "wooey.tasks.submit_script.apply_async",
            side_effect=complete_job_immediately,
        ):
            with self.captureOnCommitCallbacks(execute=True):
                queue_script_job(job.pk)

        job.refresh_from_db()
        self.assertEqual(job.status, WooeyJob.COMPLETED)


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

    def test_skips_cleanup_if_any_worker_inspection_is_unavailable(self):
        from django.utils import timezone

        wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT = timedelta(hours=24)
        wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT = timedelta(hours=1)
        wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT = 3

        for missing_inspection in ("active", "reserved", "scheduled"):
            with self.subTest(missing_inspection=missing_inspection):
                WooeyJob.objects.all().delete()
                running_job = factories.generate_job(self.translate_script)
                running_job.status = WooeyJob.RUNNING
                running_job.celery_id = "running-task-id"
                running_job.save()
                waiting_job = factories.generate_job(self.translate_script)
                waiting_job.celery_id = "waiting-task-id"
                waiting_job.save()
                WooeyJob.objects.filter(pk__in=(running_job.pk, waiting_job.pk)).update(
                    created_date=timezone.now() - timedelta(minutes=15),
                    submitted_date=timezone.now() - timedelta(minutes=15),
                    modified_date=timezone.now() - timedelta(hours=2),
                )

                worker_info = {"active": {}, "reserved": {}, "scheduled": {}}
                worker_info[missing_inspection] = None
                inspector = mock.Mock(
                    active=mock.Mock(return_value=worker_info["active"]),
                    reserved=mock.Mock(return_value=worker_info["reserved"]),
                    scheduled=mock.Mock(return_value=worker_info["scheduled"]),
                )

                with (
                    mock.patch(
                        "wooey.tasks.celery_app.control.inspect",
                        return_value=inspector,
                    ),
                    mock.patch("wooey.tasks.celery_app.control.revoke") as revoke_mock,
                    mock.patch("wooey.tasks.submit_script.apply_async") as delay_mock,
                ):
                    cleanup_stuck_jobs()

                revoke_mock.assert_not_called()
                delay_mock.assert_not_called()
                running_job.refresh_from_db()
                waiting_job.refresh_from_db()
                self.assertEqual(running_job.status, WooeyJob.RUNNING)
                self.assertEqual(waiting_job.status, WooeyJob.SUBMITTED)

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
            submitted_date=timezone.now() - timedelta(minutes=15),
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
            submitted_date=timezone.now() - timedelta(minutes=15),
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
            submitted_date=timezone.now() - timedelta(minutes=5),
            modified_date=timezone.now() - timedelta(hours=2),
        )

        with mock.patch("wooey.tasks.celery_app.control.inspect") as inspect_mock:
            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(return_value={}),
                reserved=mock.Mock(return_value={}),
                scheduled=mock.Mock(return_value={}),
            )
            with mock.patch("wooey.tasks.celery_app.control.revoke") as revoke_mock:
                with mock.patch("wooey.tasks.submit_script.apply_async") as delay_mock:
                    cleanup_stuck_jobs()
                    self.assertFalse(revoke_mock.called)
                    self.assertFalse(delay_mock.called)

        fresh_running_job.refresh_from_db()
        fresh_waiting_job.refresh_from_db()
        self.assertEqual(fresh_running_job.status, WooeyJob.RUNNING)
        self.assertEqual(fresh_waiting_job.status, WooeyJob.RETRY)

    def test_does_not_resubmit_waiting_job_with_recent_activity(self):
        from django.utils import timezone

        retry_job = factories.generate_job(self.translate_script)
        retry_job.status = WooeyJob.RETRY
        retry_job.celery_id = "active-task-id"
        retry_job.save()
        WooeyJob.objects.filter(pk=retry_job.pk).update(
            created_date=timezone.now() - timedelta(hours=2),
            submitted_date=timezone.now() - timedelta(hours=2),
            modified_date=timezone.now() - timedelta(minutes=30),
        )

        wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT = timedelta(hours=24)
        wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT = timedelta(hours=1)
        wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT = 3

        inspector = mock.Mock(
            active=mock.Mock(return_value={}),
            reserved=mock.Mock(return_value={}),
            scheduled=mock.Mock(return_value={}),
        )
        with (
            mock.patch(
                "wooey.tasks.celery_app.control.inspect",
                return_value=inspector,
            ),
            mock.patch("wooey.tasks.celery_app.control.revoke") as revoke_mock,
            mock.patch("wooey.tasks.submit_script.apply_async") as apply_async_mock,
        ):
            cleanup_stuck_jobs()

        revoke_mock.assert_not_called()
        apply_async_mock.assert_not_called()
        retry_job.refresh_from_db()
        self.assertEqual(retry_job.status, WooeyJob.RETRY)
        self.assertEqual(retry_job.retry_count, 0)

    def test_requeues_stale_waiting_jobs_and_revokes_old_task(self):
        from django.utils import timezone

        retry_job = factories.generate_job(self.translate_script)
        retry_job.status = WooeyJob.RETRY
        retry_job.celery_id = "stale-task-id"
        retry_job.retry_count = 1
        retry_job.save()
        WooeyJob.objects.filter(pk=retry_job.pk).update(
            created_date=timezone.now() - timedelta(hours=2),
            submitted_date=timezone.now() - timedelta(hours=2),
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
                with mock.patch("wooey.tasks.submit_script.apply_async") as delay_mock:
                    with self.captureOnCommitCallbacks(execute=True):
                        cleanup_stuck_jobs()
                    revoke_mock.assert_called_once_with("stale-task-id")
                    delay_mock.assert_called_once_with(
                        kwargs={
                            "wooey_job": retry_job.pk,
                            "rerun": False,
                            "submission_id": mock.ANY,
                        },
                        task_id=mock.ANY,
                    )

        retry_job.refresh_from_db()
        self.assertEqual(retry_job.status, WooeyJob.QUEUED)
        self.assertEqual(retry_job.retry_count, 2)
        self.assertEqual(
            retry_job.celery_id,
            delay_mock.call_args.kwargs["task_id"],
        )
        self.assertEqual(
            str(retry_job.submission_id),
            delay_mock.call_args.kwargs["kwargs"]["submission_id"],
        )

    def test_does_not_overwrite_newer_retry_attempt_selected_by_cleanup(self):
        from django.utils import timezone

        retry_job = factories.generate_job(self.translate_script)
        retry_job.status = WooeyJob.RETRY
        retry_job.submission_id = uuid.uuid4()
        retry_job.celery_id = "stale-task-id"
        retry_job.retry_count = 1
        retry_job.save()
        WooeyJob.objects.filter(pk=retry_job.pk).update(
            created_date=timezone.now() - timedelta(hours=2),
            submitted_date=timezone.now() - timedelta(hours=2),
            modified_date=timezone.now() - timedelta(hours=2),
        )

        wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT = timedelta(hours=24)
        wooey_settings.WOOEY_JOB_RESUBMIT_TIMEOUT = timedelta(hours=1)
        wooey_settings.WOOEY_JOB_RESUBMIT_LIMIT = 3

        newer_submission_id = uuid.uuid4()
        real_filter = WooeyJob.objects.filter
        race_applied = False

        def apply_overlapping_retry(*args, **kwargs):
            nonlocal race_applied
            if not race_applied and kwargs.get("pk") == retry_job.pk:
                race_applied = True
                real_filter(pk=retry_job.pk).update(
                    status=WooeyJob.RETRY,
                    submission_id=newer_submission_id,
                    celery_id="newer-task-id",
                    retry_count=2,
                    submitted_date=timezone.now(),
                    modified_date=timezone.now(),
                )
            return real_filter(*args, **kwargs)

        inspector = mock.Mock(
            active=mock.Mock(return_value={}),
            reserved=mock.Mock(return_value={}),
            scheduled=mock.Mock(return_value={}),
        )
        with (
            mock.patch(
                "wooey.tasks.celery_app.control.inspect",
                return_value=inspector,
            ),
            mock.patch.object(
                WooeyJob.objects,
                "filter",
                side_effect=apply_overlapping_retry,
            ),
            mock.patch("wooey.tasks.celery_app.control.revoke") as revoke_mock,
            mock.patch("wooey.tasks.submit_script.apply_async") as apply_async_mock,
            self.captureOnCommitCallbacks(execute=True),
        ):
            cleanup_stuck_jobs()

        self.assertTrue(race_applied)
        revoke_mock.assert_not_called()
        apply_async_mock.assert_not_called()
        retry_job.refresh_from_db()
        self.assertEqual(retry_job.status, WooeyJob.RETRY)
        self.assertEqual(retry_job.submission_id, newer_submission_id)
        self.assertEqual(retry_job.celery_id, "newer-task-id")
        self.assertEqual(retry_job.retry_count, 2)

    def test_does_not_requeue_jobs_already_queued_on_broker(self):
        from django.utils import timezone

        queued_job = factories.generate_job(self.translate_script)
        queued_job.status = WooeyJob.QUEUED
        queued_job.celery_id = "queued-task-id"
        queued_job.save()
        WooeyJob.objects.filter(pk=queued_job.pk).update(
            created_date=timezone.now() - timedelta(hours=2),
            submitted_date=timezone.now() - timedelta(hours=2),
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
                with mock.patch("wooey.tasks.submit_script.apply_async") as delay_mock:
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
            submitted_date=timezone.now() - timedelta(hours=25),
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
                with mock.patch("wooey.tasks.submit_script.apply_async") as delay_mock:
                    cleanup_stuck_jobs()
                    revoke_mock.assert_called_once_with("queued-task-id")
                    self.assertFalse(delay_mock.called)

        self.assertEqual(WooeyJob.objects.get(pk=queued_job.pk).status, WooeyJob.FAILED)

    def test_fresh_rerun_of_old_job_does_not_exceed_queue_timeout(self):
        from django.utils import timezone

        old_celery_setting = wooey_settings.WOOEY_CELERY
        self.addCleanup(
            setattr,
            wooey_settings,
            "WOOEY_CELERY",
            old_celery_setting,
        )
        wooey_settings.WOOEY_CELERY = True
        wooey_settings.WOOEY_JOB_QUEUE_TIMEOUT = timedelta(hours=24)

        job = factories.generate_job(self.translate_script)
        job.status = WooeyJob.COMPLETED
        job.save()
        WooeyJob.objects.filter(pk=job.pk).update(
            created_date=timezone.now() - timedelta(hours=25),
            submitted_date=timezone.now() - timedelta(hours=25),
        )
        job.refresh_from_db()

        with mock.patch("wooey.tasks.submit_script.apply_async") as delay_mock:
            with self.captureOnCommitCallbacks(execute=True):
                job.submit_to_celery(rerun=True)

        job.refresh_from_db()
        fresh_rerun_task_id = job.celery_id

        inspector = mock.Mock(
            active=mock.Mock(return_value={}),
            reserved=mock.Mock(
                return_value={"worker-id": [{"id": fresh_rerun_task_id}]}
            ),
            scheduled=mock.Mock(return_value={}),
        )
        with (
            mock.patch(
                "wooey.tasks.celery_app.control.inspect",
                return_value=inspector,
            ),
            mock.patch("wooey.tasks.celery_app.control.revoke") as revoke_mock,
        ):
            cleanup_stuck_jobs()

        revoke_mock.assert_not_called()
        job.refresh_from_db()
        self.assertEqual(job.status, WooeyJob.QUEUED)

    def test_fails_waiting_jobs_that_hit_retry_limit(self):
        from django.utils import timezone

        retry_job = factories.generate_job(self.translate_script)
        retry_job.status = WooeyJob.RETRY
        retry_job.celery_id = "stale-task-id"
        retry_job.retry_count = 3
        retry_job.save()
        WooeyJob.objects.filter(pk=retry_job.pk).update(
            created_date=timezone.now() - timedelta(hours=2),
            submitted_date=timezone.now() - timedelta(hours=2),
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
                with mock.patch("wooey.tasks.submit_script.apply_async") as delay_mock:
                    cleanup_stuck_jobs()
                    revoke_mock.assert_called_once_with("stale-task-id")
                    self.assertFalse(delay_mock.called)

        retry_job.refresh_from_db()
        self.assertEqual(retry_job.status, WooeyJob.FAILED)
