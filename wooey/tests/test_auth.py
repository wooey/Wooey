from django.test import Client, TestCase
from django.urls import reverse

from .. import settings as wooey_settings

from . import factories


class TestApiKeyLogin(TestCase):
    def test_logs_in_with_api_key(self):
        api_key = factories.APIKeyFactory()
        c = Client(HTTP_AUTHORIZATION="Bearer {}".format(api_key._api_key))
        response = c.get(reverse("wooey:wooey_home"))
        self.assertEqual(response.wsgi_request.user, api_key.profile.user)

    def test_records_last_time_api_key_used(self):
        api_key = factories.APIKeyFactory()
        c = Client(HTTP_AUTHORIZATION="Bearer {}".format(api_key._api_key))
        self.assertIsNone(api_key.last_used)
        response = c.get(reverse("wooey:wooey_home"))
        api_key.refresh_from_db()
        self.assertIsNotNone(api_key.last_used)

    def test_fails_if_api_key_inactive(self):
        api_key = factories.APIKeyFactory(active=False)
        c = Client(HTTP_AUTHORIZATION="Bearer {}".format(api_key._api_key))
        response = c.get(reverse("wooey:wooey_home"))
        self.assertNotEqual(response.wsgi_request.user, api_key.profile.user)

    def test_only_works_if_setting_is_enabled(self):
        wooey_settings.WOOEY_ENABLE_API_KEYS = False
        api_key = factories.APIKeyFactory()
        c = Client(HTTP_AUTHORIZATION="Bearer {}".format(api_key._api_key))
        response = c.get(reverse("wooey:wooey_home"))
        self.assertNotEqual(response.wsgi_request.user, api_key.profile.user)
        wooey_settings.WOOEY_ENABLE_API_KEYS = True
