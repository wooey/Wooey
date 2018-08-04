import os

from django.test import TestCase, Client

from . import factories, config, mixins, utils as test_utils
from .. import models
from .. import version


class ScriptTestCase(mixins.ScriptFactoryMixin, TestCase):

    def test_multiple_choices(self):
        # load our choice script
        script = self.choice_script

        multiple_choice_param = 'two_choices'
        single_choice_param = 'one_choice'
        optional_choice_param = 'all_choices'
        # test that we are a multiple choice entry
        param = models.ScriptParameter.objects.get(slug=multiple_choice_param)
        self.assertTrue(param.multiple_choice)

        # test our limit
        self.assertEqual(param.max_choices, 2)

        # test with a singular case
        param = models.ScriptParameter.objects.get(slug=single_choice_param)
        self.assertFalse(param.multiple_choice)
        self.assertEqual(param.max_choices, 1)

        # test cases that have variable requirements
        param = models.ScriptParameter.objects.get(slug=optional_choice_param)
        self.assertTrue(param.multiple_choice)
        self.assertEqual(param.max_choices, -1)


class ScriptGroupTestCase(TestCase):

    def test_script_group_creation(self):
        group = factories.ScriptGroupFactory()


class ScriptParameterTestCase(TestCase):
    def test_script_parameter_default(self):
        script_parameter = factories.ScriptParameterFactory()
        pk = script_parameter.pk
        for test_value in [123, 'abc', {'abc': 5}]:
            script_parameter.default = test_value
            script_parameter.save()
            self.assertEqual(models.ScriptParameter.objects.get(pk=pk).default, test_value)


class TestJob(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, mixins.FileMixin, TestCase):

    def get_local_url(self, fileinfo):
        from ..backend import utils
        local_storage = utils.get_storage(local=True)
        return local_storage.url(fileinfo['object'].filepath.name)

    def test_jobs(self):
        script = self.translate_script
        from ..backend import utils
        sequence_slug = test_utils.get_subparser_form_slug(script, 'sequence')
        out_slug = test_utils.get_subparser_form_slug(script, 'out')
        fasta_slug = test_utils.get_subparser_form_slug(script, 'fasta')
        job = utils.create_wooey_job(
            script_version_pk=script.pk,
            data={
                'job_name': 'abc',
                sequence_slug: 'aaa',
                out_slug: 'abc'
            }
        )
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
        self.assertNotEqual(old_output, new_output)
        self.assertEqual(len(old_output), len(new_output))
        # check the old entries are gone
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
        job = utils.create_wooey_job(
            script_version_pk=script.pk,
            data={
                fasta_slug: fasta_file,
                out_slug: 'abc',
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
        script = self.choice_script
        script_slug = test_utils.get_subparser_form_slug(script, 'multiple_file_choices')
        from ..backend import utils
        job = utils.create_wooey_job(script_version_pk=script.pk, data={'job_name': 'job1', script_slug: new_file})
        job = job.submit_to_celery()
        job2 = utils.create_wooey_job(script_version_pk=script.pk, data={'job_name': 'job2', script_slug: new_file})
        job2 = job2.submit_to_celery()
        job1_files = [i for i in models.UserFile.objects.filter(job=job, parameter__isnull=False) if i.parameter.parameter.form_slug == script_slug]
        job1_file = job1_files[0]
        job2_files = [i for i in models.UserFile.objects.filter(job=job2, parameter__isnull=False) if i.parameter.parameter.form_slug == script_slug]
        job2_file = job2_files[0]
        self.assertNotEqual(job1_file.pk, job2_file.pk)
        self.assertEqual(job1_file.system_file, job2_file.system_file)


    def test_multiplechoices(self):
        script = self.choice_script
        choices = [2, 1, 3]
        choice_slug = test_utils.get_subparser_form_slug(script, 'two_choices')

        from ..backend import utils
        job = utils.create_wooey_job(
            script_version_pk=script.pk,
            data={
                'job_name': 'abc',
                choice_slug: choices
            }
        )
        # make sure we have our choices in the parameters
        choice_params = [i.value for i in job.get_parameters() if i.parameter.form_slug == choice_slug]
        self.assertEqual(choices, choice_params)
        job = job.submit_to_celery()


class TestCustomWidgets(TestCase):
    def test_widget_attributes(self):
        widget = factories.WooeyWidgetFactory(
            input_properties='custom-property',
            input_attributes='attr1="custom1" attr2="custom2"',
            input_class='custom-class',
        )
        self.assertEquals(
            widget.widget_attributes,
            {
                'custom-property': True,
                'attr1': 'custom1',
                'attr2': 'custom2',
                'class': 'custom-class',
            }
        )