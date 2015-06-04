import os

from django.test import TestCase

from . import factories, config, mixins

class ScriptTestCase(mixins.ScriptFactoryMixin, TestCase):

    def test_script_creation(self):
        script = factories.TranslateScriptFactory()


class ScriptGroupTestCase(TestCase):

    def test_script_group_creation(self):
        group = factories.ScriptGroupFactory()


class TestJob(mixins.ScriptFactoryMixin, TestCase):
    def test_jobs(self):
        script = factories.TranslateScriptFactory()
        from ..backend import utils
        from .. import settings
        # the test server doesn't have celery running
        settings.DJANGUI_CELERY = False
        job = utils.create_djangui_job({'djangui_type': script.pk, 'user': None, 'job_name': 'abc', 'sequence': 'aaa', 'out': 'abc'})
        job = job.submit_to_celery()
        old_pk = job.pk
        new_job = job.submit_to_celery(resubmit=True)
        self.assertNotEqual(old_pk, new_job.pk)
        # test job with a file
        job = utils.create_djangui_job({'djangui_type': script.pk, 'user': None, 'job_name': 'abc',
                                        'fasta': open(os.path.join(config.DJANGUI_TEST_DATA, 'fasta.fasta')),
                                        'out': 'abc'})