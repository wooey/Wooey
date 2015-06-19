import os

from django.test import TestCase, Client

from . import factories, config, mixins
from .. import version

class ScriptTestCase(mixins.ScriptFactoryMixin, TestCase):

    def test_script_creation(self):
        script = factories.TranslateScriptFactory()


class ScriptGroupTestCase(TestCase):

    def test_script_group_creation(self):
        group = factories.ScriptGroupFactory()


class TestJob(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    urls = 'djangui.test_urls'

    def test_jobs(self):
        script = factories.TranslateScriptFactory()
        from ..backend import utils
        from .. import settings
        # the test server doesn't have celery running
        settings.WOOEY_CELERY = False
        job = utils.create_wooey_job(script_pk=script.pk, data={'job_name': 'abc', 'sequence': 'aaa', 'out': 'abc'})
        job = job.submit_to_celery()
        old_pk = job.pk
        new_job = job.submit_to_celery(resubmit=True)
        self.assertNotEqual(old_pk, new_job.pk)
        # test rerunning, our output should be removed
        from ..models import WooeyFile
        old_output = sorted([i.pk for i in WooeyFile.objects.filter(job=new_job)])
        job.submit_to_celery(rerun=True)
        # check that we overwrite our output
        new_output = sorted([i.pk for i in WooeyFile.objects.filter(job=new_job)])
        # Django 1.6 has a bug where they are reusing pk numbers
        if version.DJANGO_VERSION >= version.DJ17:
            self.assertNotEqual(old_output, new_output)
        self.assertEqual(len(old_output), len(new_output))
        # check the old entries are gone
        if version.DJANGO_VERSION >= version.DJ17:
            # Django 1.6 has a bug where they are reusing pk numbers, so once again we cannot use this check
            self.assertEqual([], list(WooeyFile.objects.filter(pk__in=old_output)))

        # check our download links are ok
        job = utils.create_wooey_job(script_pk=script.pk,
                                        data={'fasta': open(os.path.join(config.WOOEY_TEST_DATA, 'fasta.fasta')),
        file_previews = utils.get_file_previews(job)
        for group, files in file_previews.items():
            for fileinfo in files:
                response = Client().get(fileinfo.get('url'))
                self.assertEqual(response.status_code, 200)

                                        'out': 'abc', 'job_name': 'abc'})
