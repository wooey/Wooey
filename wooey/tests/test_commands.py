import os

from django.core.management import call_command
from django.test import TestCase

from ..models import ScriptVersion

from . import config
from . import mixins


class CommandTests(mixins.ScriptFactoryMixin, TestCase):
    def setUp(self):
        # don't setup scripts, but we want to still tear down after each test
        pass

    def test_addscript(self):
        call_command('addscript', os.path.join(config.WOOEY_TEST_SCRIPTS, 'choices.py'))
        # Test we can update the script
        script_version = ScriptVersion.objects.latest('created_date')
        old_parameters = list(script_version.get_parameters())
        call_command('addscript', '--update', os.path.join(config.WOOEY_TEST_SCRIPTS, 'choices.py'))
        new_version = ScriptVersion.objects.latest('created_date')

        # make sure we updated
        self.assertEqual(new_version.script_iteration, script_version.script_iteration + 1)

        # Make sure the parameters have not changed
        self.assertListEqual(old_parameters, list(new_version.get_parameters()))
