import os
from datetime import timedelta

from django.test import TestCase

from wooey import settings as wooey_settings
from wooey.backend.utils import add_wooey_script
from wooey.tasks import get_latest_script

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
