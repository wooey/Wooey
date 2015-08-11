import os

from django.test import TestCase, Client

from . import factories, config, mixins
from .. import version

class ScriptTestCase(mixins.ScriptFactoryMixin, TestCase):

    def test_script_creation(self):
        script = factories.TranslateScriptFactory()

    def test_multiple_choices(self):
        # load our choice script
        script = factories.ChoiceScriptFactory()

        multiple_choice_param = 'two_choices'
        single_choice_param = 'one_choice'
        optional_choice_param = 'all_choices'
        # test that we are a multiple choice entry
        from ..models import ScriptParameter
        param = ScriptParameter.objects.get(slug=multiple_choice_param)
        self.assertTrue(param.multiple_choice)

        # test our limit
        self.assertEqual(param.max_choices, 2)

        # test with a singular case
        param = ScriptParameter.objects.get(slug=single_choice_param)
        self.assertFalse(param.multiple_choice)
        self.assertEqual(param.max_choices, 1)

        # test cases that have variable requirements
        param = ScriptParameter.objects.get(slug=optional_choice_param)
        self.assertTrue(param.multiple_choice)
        self.assertEqual(param.max_choices, -1)

class ScriptGroupTestCase(TestCase):

    def test_script_group_creation(self):
        group = factories.ScriptGroupFactory()


class TestJob(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    urls = 'wooey.test_urls'

    def setUp(self):
        from .. import settings
        # the test server doesn't have celery running
        settings.WOOEY_CELERY = False

    def test_jobs(self):
        script = factories.TranslateScriptFactory()
        from ..backend import utils
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

        file_previews = utils.get_file_previews(job)
        for group, files in file_previews.items():
            for fileinfo in files:
                response = Client().get(fileinfo.get('url'))
                self.assertEqual(response.status_code, 200)

        # check our download links are ok
        job = utils.create_wooey_job(script_pk=script.pk,
                                        data={'fasta': open(os.path.join(config.WOOEY_TEST_DATA, 'fasta.fasta')),
                                              'out': 'abc', 'job_name': 'abc'})

        # check our upload link is ok
        file_previews = utils.get_file_previews(job)
        for group, files in file_previews.items():
            for fileinfo in files:
                response = Client().get(fileinfo.get('url'))
                self.assertEqual(response.status_code, 200)

    def test_multiplechoices(self):
        script = factories.ChoiceScriptFactory()
        choices = ['2', '1', '3']
        choice_param = 'two_choices'

        from ..backend import utils
        job = utils.create_wooey_job(script_pk=script.pk, data={'job_name': 'abc', choice_param: choices})
        # make sure we have our choices in the parameters
        choice_params = [i.value for i in job.get_parameters() if i.parameter.slug == choice_param]
        self.assertEqual(choices, choice_params)
        job = job.submit_to_celery()
