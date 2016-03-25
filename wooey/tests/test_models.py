import os
import uuid

from django.test import TestCase, Client

from . import factories, config, mixins
from .. import version


class ScriptTestCase(mixins.ScriptFactoryMixin, TestCase):

    def test_multiple_choices(self):
        # load our choice script
        script = self.choice_script

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


class TestJob(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, mixins.FileMixin, TestCase):
    urls = 'wooey.test_urls'

    def get_local_url(self, fileinfo):
        from ..backend import utils
        local_storage = utils.get_storage(local=True)
        return local_storage.url(fileinfo['object'].filepath.name)

    def test_jobs(self):
        script = self.translate_script
        from ..backend import utils
        job = utils.create_wooey_job(script_version_pk=script.pk, data={'job_name': 'abc', 'sequence': 'aaa', 'out': 'abc'})
        job = job.submit_to_celery()
        old_pk = job.pk
        new_job = job.submit_to_celery(resubmit=True)
        self.assertNotEqual(old_pk, new_job.pk)
        # test rerunning, our output should be removed
        from ..models import UserFile
        old_output = sorted([i.pk for i in UserFile.objects.filter(job=new_job)])
        # the pk will not change here since we are using rerun=True
        new_job.submit_to_celery(rerun=True)
        # check that we overwrite our output
        new_output = sorted([i.pk for i in UserFile.objects.filter(job=new_job)])
        # Django 1.6 has a bug where they are reusing pk numbers
        if version.DJANGO_VERSION >= version.DJ17:
            self.assertNotEqual(old_output, new_output)
        self.assertEqual(len(old_output), len(new_output))
        # check the old entries are gone
        if version.DJANGO_VERSION >= version.DJ17:
            # Django 1.6 has a bug where they are reusing pk numbers, so once again we cannot use this check
            self.assertEqual([], list(UserFile.objects.filter(pk__in=old_output)))

        file_previews = utils.get_file_previews(job)
        for group, files in file_previews.items():
            for fileinfo in files:
                # for testing, we use the local url
                response = Client().get(self.get_local_url(fileinfo))
                self.assertEqual(response.status_code, 200)

        # check our download links are ok
        # upload the file first to our storage engine so this works in tests
        local_storage = utils.get_storage(local=True)
        fasta_path = local_storage.save('fasta.fasta', open(os.path.join(config.WOOEY_TEST_DATA, 'fasta.fasta')))
        fasta_file = local_storage.open(fasta_path)
        job = utils.create_wooey_job(script_version_pk=script.pk,
                                        data={
                                            'fasta': fasta_file,
                                            'out': 'abc',
                                            'job_name': 'abc'
                                        }
                                     )

        # check our upload link is ok
        file_previews = utils.get_file_previews(job)
        for group, files in file_previews.items():
            for fileinfo in files:
                response = Client().get(self.get_local_url(fileinfo))
                self.assertEqual(response.status_code, 200)

    def test_file_sharing(self):
        # this tests whether a file uploaded by one job will be referenced by a second job instead of being duplicated
        # on the file system
        new_file = self.storage.open(self.get_any_file())
        script_slug = 'multiple_file_choices'
        script = self.choice_script
        from ..backend import utils
        job = utils.create_wooey_job(script_version_pk=script.pk, data={'job_name': 'job1', script_slug: new_file})
        job = job.submit_to_celery()
        job2 = utils.create_wooey_job(script_version_pk=script.pk, data={'job_name': 'job2', script_slug: new_file})
        job2 = job2.submit_to_celery()
        from ..models import UserFile
        job1_files = [i for i in UserFile.objects.filter(job=job, parameter__isnull=False) if i.parameter.parameter.slug == script_slug]
        job1_file = job1_files[0]
        job2_files = [i for i in UserFile.objects.filter(job=job2, parameter__isnull=False) if i.parameter.parameter.slug == script_slug]
        job2_file = job2_files[0]
        self.assertNotEqual(job1_file.pk, job2_file.pk)
        self.assertEqual(job1_file.system_file, job2_file.system_file)


    def test_multiplechoices(self):
        script = self.choice_script
        choices = ['2', '1', '3']
        choice_param = 'two_choices'

        from ..backend import utils
        job = utils.create_wooey_job(script_version_pk=script.pk, data={'job_name': 'abc', choice_param: choices})
        # make sure we have our choices in the parameters
        choice_params = [i.value for i in job.get_parameters() if i.parameter.slug == choice_param]
        self.assertEqual(choices, choice_params)
        job = job.submit_to_celery()
