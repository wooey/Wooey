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
    cleanup_dead_jobs,
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


class TestGetLatestScript(mixins.FileMixin, mixins.ScriptTearDown, TestCase):
    def setUp(self):
        super(TestGetLatestScript, self).setUp()
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'versioned_script', 'v1.py')
        with open(script) as o:
            v1 = self.storage.save(self.filename_func('v1.py'), o)
        res = add_wooey_script(script_path=v1, script_name='test_versions')
        self.first_version = self.rename_script(res['script'])

    def rename_script(self, script_version):
        # Because we are on local storage, the script uploaded will already be present, so
        # we rename it to mimic it being absent on a worker node
        new_name = self.storage.save(script_version.script_path.name, script_version.script_path.file)
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
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'versioned_script', 'v2.py')
        with open(script) as o:
            v2 = self.storage.save(self.filename_func('v2.py'), o)

        res = add_wooey_script(script_path=v2, script_name='test_versions')
        second_version = self.rename_script(res['script'])

        self.assertTrue(get_latest_script(second_version))


class TestCleanupDeadJobs(mixins.ScriptFactoryMixin, TestCase):
    def test_handles_unresponsive_workers(self):
        # Ensure that if we cannot connect to celery, we do nothing.
        with mock.patch('wooey.tasks.celery_app.control.inspect') as inspect_mock:
            running_job = factories.generate_job(self.translate_script)
            running_job.status = WooeyJob.RUNNING
            running_job.save()

            inspect_mock.return_value = mock.Mock(
                active=mock.Mock(
                    return_value=None,
                )
            )
            cleanup_dead_jobs()
            self.assertEqual(WooeyJob.objects.get(pk=running_job.id).status, WooeyJob.RUNNING)

    def test_cleans_up_dead_jobs(self):
        # Make a job that is running but not active, and a job that is running and active.
        dead_job = factories.generate_job(self.translate_script)
        dead_job.status = WooeyJob.RUNNING
        dead_job.save()
        active_job = factories.generate_job(self.translate_script)
        active_job.status = WooeyJob.RUNNING
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
            cleanup_dead_jobs()

            # Assert the dead job is updated
            self.assertEqual(WooeyJob.objects.get(pk=dead_job.id).status, WooeyJob.FAILED)
            self.assertEqual(WooeyJob.objects.get(pk=active_job.id).status, WooeyJob.RUNNING)
