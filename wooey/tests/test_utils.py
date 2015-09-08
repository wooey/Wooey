import os

from django.test import TestCase

from ..backend import utils

from . import factories
from . import config
from . import mixins


class TestUtils(mixins.ScriptFactoryMixin, TestCase):
    def test_sanitize_name(self):
        assert(utils.sanitize_name('abc')) == 'abc'
        assert(utils.sanitize_name('ab c')) == 'ab_c'
        assert(utils.sanitize_name('ab-c')) == 'ab_c'

    def test_sanitize_string(self):
        assert(utils.sanitize_string('ab"c')) == 'ab\\"c'

    def test_add_script(self):
        pass
        # TODO: fix me
        # utils.add_wooey_script(script=os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate.py'))

    def test_anonymous_users(self):
        from .. import settings as wooey_settings
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
        script_version = self.translate_script
        script = script_version.script
        d = utils.valid_user(script, user)
        self.assertTrue(d['valid'])
        wooey_settings.WOOEY_ALLOW_ANONYMOUS = False
        d = utils.valid_user(script, user)
        self.assertFalse(d['valid'])

    def test_valid_user(self):
        user = factories.UserFactory()
        script_version = self.translate_script
        script = script_version.script
        d = utils.valid_user(script, user)
        self.assertTrue(d['valid'])
        from .. import settings as wooey_settings
        self.assertEqual('disabled', d['display'])
        wooey_settings.WOOEY_SHOW_LOCKED_SCRIPTS = False
        d = utils.valid_user(script, user)
        self.assertEqual('hide', d['display'])
        from django.contrib.auth.models import Group
        test_group = Group(name='test')
        test_group.save()
        script.user_groups.add(test_group)
        d = utils.valid_user(script, user)
        self.assertFalse(d['valid'])
        user.groups.add(test_group)
        d = utils.valid_user(script, user)
        self.assertTrue(d['valid'])


class TestFileDetectors(TestCase):
    def test_detector(self):
        self.file = os.path.join(config.WOOEY_TEST_DATA, 'fasta.fasta')
        res, preview = utils.test_fastx(self.file)
        self.assertEqual(res, True, 'Fastx parser fail')
        self.assertEqual(preview, open(self.file).readlines(), 'Fastx Preview Fail')

    def test_delimited(self):
        self.file = os.path.join(config.WOOEY_TEST_DATA, 'delimited.tsv')
        res, preview = utils.test_delimited(self.file)
        self.assertEqual(res, True, 'Delimited parser fail')
        self.assertEqual(preview, [i.strip().split('\t') for i in open(self.file).readlines()], 'Delimited Preview Fail')
