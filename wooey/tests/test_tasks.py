import mock
from datetime import timedelta

from django.test import TestCase

from . import mixins, factories
from .. import (
    models,
    settings as wooey_settings,
    tasks,
)


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
        wooey_settings.WOOEY_JOB_EXPIRATION.update({
            'user': timedelta(hours=1),
            'anonymous': timedelta(hours=1),
        })
        cleanup_wooey_jobs()
        self.assertListEqual(list(WooeyJob.objects.all()), [anon_job, user_job])
        time.sleep(0.1)
        wooey_settings.WOOEY_JOB_EXPIRATION.update({
            'user': timedelta(hours=1),
            'anonymous': timedelta(microseconds=1),
        })
        cleanup_wooey_jobs()
        self.assertListEqual(list(WooeyJob.objects.all()), [user_job])

        wooey_settings.WOOEY_JOB_EXPIRATION.update({
            'user': timedelta(microseconds=1),
            'anonymous': timedelta(microseconds=1),
        })

        cleanup_wooey_jobs()
        self.assertListEqual(list(WooeyJob.objects.all()), [])

class TestCleanupDeadJobs(mixins.ScriptFactoryMixin, TestCase):
    def test_handles_unresponsive_workers(self):
        with mock.patch('wooey.tasks.celery_app.control.inspect') as inspect_mock:
            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(
                    return_value=None,
                )
            )
            tasks.cleanup_dead_jobs()

    def test_cleans_up_dead_jobs(self):
        # Make a job that is running but not active, and a job that is running and active.
        dead_job = factories.generate_job(self.translate_script)
        dead_job.status = models.WooeyJob.RUNNING
        dead_job.save()
        active_job = factories.generate_job(self.translate_script)
        active_job.status = models.WooeyJob.RUNNING
        active_job.celery_id = 'celery-id'
        active_job.save()
        with mock.patch('wooey.tasks.celery_app.control.inspect') as inspect_mock:
            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(
                    return_value={
                        'worker-id': [
                            {
                                'id': active_job.celery_id,
                            }
                        ]
                    },
                )
            )
            tasks.cleanup_dead_jobs()

            # Assert the dead job is updated
            self.assertEqual(models.WooeyJob.objects.get(pk=dead_job.id).status, models.WooeyJob.FAILED)
            self.assertEqual(models.WooeyJob.objects.get(pk=active_job.id).status, models.WooeyJob.RUNNING)