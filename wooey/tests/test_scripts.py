import os

from django.test import TestCase
from django.conf import settings

from . import config, mixins
from ..backend import utils
from ..models import Script
from .. import settings as wooey_settings

class ScriptAdditionTests(mixins.ScriptFactoryMixin, TestCase):

    def test_command_order(self):
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'command_order.py')
        new_file = utils.get_storage(local=True).save(os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, 'command_order.py'), open(script))
        new_file = utils.get_storage(local=True).path(new_file)
        added, errors = utils.add_wooey_script(script=new_file, group=None)
        self.assertEqual(added, True, errors)
        job = utils.create_wooey_job(script_pk=1, data={'job_name': 'abc', 'link': 'alink', 'name': 'aname'})
        # These are positional arguments -- we DO NOT want them returning anything
        self.assertEqual(['', ''], [i.parameter.short_param for i in job.get_parameters()])
        # These are the params shown to the user, we want them returning their destination
        # This also checks that we maintain the expected order
        self.assertEqual(['link', 'name'], [i.parameter.script_param for i in job.get_parameters()])
        # Check the job command
        commands = utils.get_job_commands(job=job)[2:]
        self.assertEqual(['alink', 'aname'], commands)

    def test_script_upgrade(self):
        script_path = os.path.join(config.WOOEY_TEST_SCRIPTS, 'command_order.py')
        new_file = utils.get_storage(local=True).save(os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, 'command_order.py'), open(script_path))
        new_file = utils.get_storage(local=True).path(new_file)
        added, errors = utils.add_wooey_script(script=new_file, group=None)
        self.assertEqual(added, True, errors)
        # upgrade script
        script = Script.objects.get(pk=1)
        new_script = utils.get_storage(local=True).save(os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, 'command_order.py'), open(script_path))
        new_script = utils.get_storage(local=True).path(new_script)
        script.script_path = new_script
        # we are going to be cloning this, so we lose the old object
        old_pk, old_version = script.pk, script.script_version
        script.save()
        self.assertNotEqual(old_pk, script.pk)
        self.assertNotEqual(old_version, script.script_version)
        # asset we are using the latest script in the frontend
        self.assertIn(script, settings.WOOEY_SCRIPTS)
        old_script = Script.objects.get(pk=old_pk)
        self.assertNotIn(old_script, settings.WOOEY_SCRIPTS)
