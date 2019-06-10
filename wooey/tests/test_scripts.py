import mock
import os

from django.test import TestCase

from . import config, mixins, utils as test_utils
from ..backend import utils
from ..models import ScriptParameter, ScriptVersion


class ScriptAdditionTests(mixins.ScriptFactoryMixin, mixins.FileMixin, TestCase):

    def test_command_order(self):
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'command_order.py')
        with open(script) as o:
            new_file = self.storage.save(self.filename_func('command_order.py'), o)
        res = utils.add_wooey_script(script_path=new_file, group=None)
        self.assertEqual(res['valid'], True, res['errors'])
        link_slug = test_utils.get_subparser_form_slug(res['script'], 'link')
        name_slug = test_utils.get_subparser_form_slug(res['script'], 'name')
        job = utils.create_wooey_job(
            script_version_pk=res['script'].pk,
            data={
                'job_name': 'abc',
                link_slug: 'alink',
                name_slug: 'aname'
            }
        )
        # These are positional arguments -- we DO NOT want them returning anything
        self.assertEqual(['', ''], [i.parameter.short_param for i in job.get_parameters()])
        # These are the params shown to the user, we want them returning their destination
        # This also checks that we maintain the expected order
        self.assertEqual(['link', 'name'], [i.parameter.script_param for i in job.get_parameters()])
        # Check the job command
        commands = utils.get_job_commands(job=job)[2:]
        self.assertEqual(['alink', 'aname'], commands)

    def test_default_parameters(self):
        script_path = os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate.py')
        with open(script_path) as o:
            new_file = self.storage.save(self.filename_func('translate.py'), o)
        res = utils.add_wooey_script(script_path=new_file, group=None)
        script_version = res['script']
        script_parameter = script_version.scriptparameter_set.get(script_param='frame')
        self.assertEqual(script_parameter.default, '+1')

    def test_collapse_arguments(self):
        slug = test_utils.get_subparser_form_slug(self.choice_script, 'need_at_least_one_numbers')
        job = utils.create_wooey_job(
            script_version_pk=self.choice_script.pk,
            data={
                'job_name': 'abc',
                slug: [1, 2]
            }
        )
        commands = utils.get_job_commands(job=job)[2:]
        self.assertEqual(commands, ['--need-at-least-one-numbers', '1', '--need-at-least-one-numbers', '2'])

        slug = test_utils.get_subparser_form_slug(self.choice_script, 'choices_str')
        job = utils.create_wooey_job(
            script_version_pk=self.choice_script.pk,
            data={
                'job_name': 'abc',
                slug: [1, 2, 3]
            }
        )
        commands = utils.get_job_commands(job=job)[2:]
        self.assertEqual(commands, ['--choices-str', '1', '2', '3'])

    def test_script_upgrade(self):
        script_path = os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate.py')
        with open(script_path) as o:
            new_file = self.storage.save(self.filename_func('translate.py'), o)
        res = utils.add_wooey_script(script_path=new_file, group=None)
        self.assertEqual(res['valid'], True, res['errors'])
        # upgrade script
        script = ScriptVersion.objects.get(pk=res['script'].pk)
        script_path2 = os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate2.py')
        with open(script_path2) as o:
            new_script = self.storage.save(self.filename_func('translate2.py'), o)
        script.script_path = new_script
        # we are going to be cloning this, so we lose the old object
        old_pk, old_iter = script.pk, script.script_iteration
        script.save()
        self.assertNotEqual(old_pk, script.pk)
        self.assertNotEqual(old_iter, script.script_iteration)
        # asset we are using the latest script in the frontend
        self.assertIn(script, [i.latest_version for i in utils.get_current_scripts()])
        old_script = ScriptVersion.objects.get(pk=old_pk)
        self.assertNotIn(old_script, [i.latest_version for i in utils.get_current_scripts()])

    def test_script_parameter_upgrade(self):
        script_path = os.path.join(config.WOOEY_TEST_SCRIPTS, 'choices.py')
        script_2_path = os.path.join(config.WOOEY_TEST_SCRIPTS, 'choices_2.py')

        # Upload the script
        with open(script_path) as o:
            new_file = self.storage.save(self.filename_func('choices.py'), o)
        res = utils.add_wooey_script(script_path=new_file, group=None)
        self.assertEqual(res['valid'], True, res['errors'])

        # upgrade script
        script = ScriptVersion.objects.get(pk=res['script'].pk)
        with open(script_2_path) as o:
            new_script = self.storage.save(self.filename_func('choices.py'), o)
        script.script_path = new_script
        # we are going to be cloning this, so we lose the old object and we keep a reference here
        old_pk, old_iter = script.pk, script.script_iteration
        script.save()

        self.assertNotEqual(old_pk, script.pk)
        self.assertNotEqual(old_iter, script.script_iteration)
        # asset we are using the latest script in the frontend
        self.assertIn(script, [i.latest_version for i in utils.get_current_scripts()])
        old_script = ScriptVersion.objects.get(pk=old_pk)
        self.assertNotIn(old_script, [i.latest_version for i in utils.get_current_scripts()])
        # Assert that the 'one_choice' parameter is different between the versions, but all else is the same
        old_parameters = list(old_script.get_parameters())
        new_parameters = list(script.get_parameters())
        self.assertListEqual(old_parameters[1:], new_parameters[1:])
        self.assertTrue(new_parameters[0].short_param, '--one-choice-added')
        self.assertTrue(old_parameters[0].short_param, '--one-choice')

    def test_redownloads_on_script_update(self):
        # Run the translate script, update it, and ensure the new version is downloaded
        sequence_slug = test_utils.get_subparser_form_slug(self.translate_script, 'sequence')
        job = utils.create_wooey_job(script_version_pk=self.translate_script.pk, data={'job_name': 'job1', sequence_slug: 'ATG'})
        job = job.submit_to_celery()

        # The file has been downloaded locally, update the script and ensure the new one is used
        script_path2 = os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate2.py')
        with open(script_path2) as o:
            new_script = self.storage.save(self.filename_func('translate2.py'), o)
        self.translate_script.script_path = new_script
        self.translate_script.save()

        job = utils.create_wooey_job(script_version_pk=self.translate_script.pk,
                                     data={'job_name': 'job1', sequence_slug: 'ATC'})
        with mock.patch('wooey.backend.utils.default_storage.local_storage.save') as storage_save:
            job.submit_to_celery()
            storage_save.assert_called()

    def test_reuses_script_if_not_updated(self):
        sequence_slug = test_utils.get_subparser_form_slug(self.translate_script, 'sequence')
        job = utils.create_wooey_job(script_version_pk=self.translate_script.pk,
                                     data={'job_name': 'job1', sequence_slug: 'ATG'})
        job.submit_to_celery()

        job = utils.create_wooey_job(script_version_pk=self.translate_script.pk,
                                     data={'job_name': 'job2', sequence_slug: 'ATC'})
        with mock.patch('wooey.backend.utils.default_storage.local_storage.save') as storage_save:
            job.submit_to_celery()
            storage_save.assert_not_called()