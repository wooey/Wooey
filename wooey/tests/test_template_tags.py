import os

from django.test import TestCase

from . import config
from ..templatetags import wooey_tags
from .. import settings as wooey_settings


class TemplateTagsTestCase(TestCase):

    def test_get_wooey_setting(self):
        #test that get_wooey_setting works as expected
        self.assertEqual(wooey_tags.get_wooey_setting("WOOEY_SITE_NAME"), wooey_settings.WOOEY_SITE_NAME)
        #test that get_wooey_setting works following a change
        wooey_settings.WOOEY_SITE_NAME = "TEST_SITE"
        self.assertEqual(wooey_tags.get_wooey_setting("WOOEY_SITE_NAME"), wooey_settings.WOOEY_SITE_NAME)
