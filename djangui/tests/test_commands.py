import os

from django.test import TestCase

from . import config

class FormTestCase(TestCase):

    def test_addscript(self):
        from django.core.management import call_command
        call_command('addscript', os.path.join(config.DJANGUI_TEST_SCRIPTS, 'command_order.py'))