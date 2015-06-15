import os

from django.test import TestCase

from . import factories, config, mixins
from .. import version

class ScriptTestCase(mixins.ScriptFactoryMixin, TestCase):

    def test_script_creation(self):
        script = factories.TranslateScriptFactory()


class ScriptGroupTestCase(TestCase):

    def test_script_group_creation(self):
        group = factories.ScriptGroupFactory()


class TestJob(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    def test_jobs(self):
        script = factories.TranslateScriptFactory()
        from ..backend import utils
        from .. import settings
        # the test server doesn't have celery running
        settings.DJANGUI_CELERY = False
        job = utils.create_djangui_job(script_pk=script.pk, data={'job_name': 'abc', 'sequence': 'aaa', 'out': 'abc'})
        job = job.submit_to_celery()
        old_pk = job.pk
        new_job = job.submit_to_celery(resubmit=True)
        self.assertNotEqual(old_pk, new_job.pk)
        # test rerunning, our output should be removed
        from ..models import DjanguiFile
        old_output = sorted([i.pk for i in DjanguiFile.objects.filter(job=new_job)])
        job.submit_to_celery(rerun=True)
        # check that we overwrite our output
        new_output = sorted([i.pk for i in DjanguiFile.objects.filter(job=new_job)])
        # Django 1.6 has a bug where they are reusing pk numbers
        if version.DJANGO_VERSION >= version.DJ17:
            self.assertNotEqual(old_output, new_output)
        self.assertEqual(len(old_output), len(new_output))
        # check the old entries are gone
        if version.DJANGO_VERSION >= version.DJ17:
            # Django 1.6 has a bug where they are reusing pk numbers, so once again we cannot use this check
            self.assertEqual([], list(DjanguiFile.objects.filter(pk__in=old_output)))
        job = utils.create_djangui_job(script_pk=script.pk,
                                        data={'fasta': open(os.path.join(config.DJANGUI_TEST_DATA, 'fasta.fasta')),
                                        'out': 'abc', 'job_name': 'abc'})