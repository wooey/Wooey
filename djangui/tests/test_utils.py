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

class TestFileDetectors(TestCase):
    def test_detector(self):
        self.file = os.path.join(config.DJANGUI_TEST_DATA, 'fasta.fasta')
        res, preview = utils.test_fastx(self.file)
        self.assertEqual(res, True, 'Fastx parser fail')
        self.assertEqual(preview, open(self.file).readlines(), 'Fastx Preview Fail')

    def test_delimited(self):
        self.file = os.path.join(config.DJANGUI_TEST_DATA, 'delimited.tsv')
        res, preview = utils.test_delimited(self.file)
        self.assertEqual(res, True, 'Delimited parser fail')
        self.assertEqual(preview, [i.strip().split('\t') for i in open(self.file).readlines()], 'Delimited Preview Fail')