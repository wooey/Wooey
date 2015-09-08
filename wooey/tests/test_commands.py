import os

from django.test import TestCase

from . import config
from ..backend import utils
from . import mixins


class FormTestCase(mixins.ScriptFactoryMixin, TestCase):

    def test_addscript(self):
        from django.core.management import call_command
        call_command('addscript', os.path.join(config.WOOEY_TEST_SCRIPTS, 'command_order.py'))
