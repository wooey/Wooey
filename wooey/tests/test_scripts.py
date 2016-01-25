import os

from django.test import TestCase
from django.conf import settings

from . import config, mixins
from ..backend import utils
from ..models import ScriptVersion
from .. import settings as wooey_settings


class ScriptAdditionTests(mixins.ScriptFactoryMixin, TestCase):
    def setUp(self):
        self.storage = utils.get_storage(local=not wooey_settings.WOOEY_EPHEMERAL_FILES)
        self.filename_func = lambda x: os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, x)

    def test_command_order(self):
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'command_order.py')
        with open(script) as o:
            new_file = self.storage.save(self.filename_func('command_order.py'), o)
        res = utils.add_wooey_script(script_path=new_file, group=None)
        self.assertEqual(res['valid'], True, res['errors'])
        job = utils.create_wooey_job(script_version_pk=1, data={'job_name': 'abc', 'link': 'alink', 'name': 'aname'})
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
        with open(script_path) as o:
            new_file = self.storage.save(self.filename_func('command_order.py'), o)
        res = utils.add_wooey_script(script_path=new_file, group=None)
        self.assertEqual(res['valid'], True, res['errors'])
        # upgrade script
        script = ScriptVersion.objects.get(pk=1)
        with open(script_path) as o:
            new_script = self.storage.save(self.filename_func('command_order.py'), o)
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
