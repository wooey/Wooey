from django.template import Context
from django.test import TestCase

from ..django_compat import get_template_from_string
from ..templatetags import wooey_tags
from .. import settings as wooey_settings
from .factories import UserFactory


class TemplateTagsTestCase(TestCase):

    def test_get_wooey_setting(self):
        #test that get_wooey_setting works as expected
        self.assertEqual(wooey_tags.get_wooey_setting("WOOEY_SITE_NAME"), wooey_settings.WOOEY_SITE_NAME)
        #test that get_wooey_setting works following a change
        wooey_settings.WOOEY_SITE_NAME = "TEST_SITE"
        self.assertEqual(wooey_tags.get_wooey_setting("WOOEY_SITE_NAME"), wooey_settings.WOOEY_SITE_NAME)


    def test_gravatar(self):
        t = get_template_from_string("{% load wooey_tags %}{% gravatar user.email 64 %}")
        user = UserFactory()
        self.assertEqual(
            t.render(Context({'user': user})),
            "http://www.gravatar.com/avatar/d10ca8d11301c2f4993ac2279ce4b930?s=64"
        )
        