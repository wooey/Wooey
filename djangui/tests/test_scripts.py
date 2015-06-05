import os

from django.test import TestCase

from . import config, mixins
from ..backend import utils
from .. import settings as djangui_settings

class ScriptAdditionTests(mixins.ScriptFactoryMixin, TestCase):

    def test_command_order(self):
        script = os.path.join(config.DJANGUI_TEST_SCRIPTS, 'command_order.py')
        new_file = utils.get_storage(local=True).save(os.path.join(djangui_settings.DJANGUI_SCRIPT_DIR, 'command_order.py'), open(script))
        added, errors = utils.add_djangui_script(script=new_file, group=None)
        self.assertEqual(added, True, errors)
        job = utils.create_djangui_job({'djangui_type': 1, 'user': None, 'job_name': 'abc', 'link': 'alink', 'name': 'aname'})
        # These are positional arguments -- we DO NOT want them returning anything
        self.assertEqual(['', ''], [i.parameter.short_param for i in job.get_parameters()])
        # These are the params shown to the user, we want them returning their destination
        # This also checks that we maintain the expected order
        self.assertEqual(['link', 'name'], [i.parameter.script_param for i in job.get_parameters()])
        # Check the job command
        commands = utils.get_job_commands(job=job)[2:]
        self.assertEqual(['alink', 'aname'], commands)