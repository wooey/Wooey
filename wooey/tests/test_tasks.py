from datetime import timedelta

from django.test import TestCase

from . import mixins, factories
from .. import settings as wooey_settings


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
