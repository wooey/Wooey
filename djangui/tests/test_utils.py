import os

from django.test import TestCase

from ..backend import utils

from . import factories
from . import config

class TestUtils(TestCase):
    def test_sanitize_name(self):
        assert(utils.sanitize_name('abc')) == 'abc'
        assert(utils.sanitize_name('ab c')) == 'ab_c'
        assert(utils.sanitize_name('ab-c')) == 'ab_c'

    def test_sanitize_string(self):
        assert(utils.sanitize_string('ab"c')) == 'ab\\"c'

    def test_add_script(self):
        pass
        # TODO: fix me
        # utils.add_djangui_script(script=os.path.join(config.DJANGUI_TEST_SCRIPTS, 'translate.py'))