from django.test import Client, TestCase
from django.urls import reverse

from . import factories


class TestApiKeyLogin(TestCase):
    def test_logs_in_with_api_key(self):
        api_key = factories.APIKeyFactory()
        c = Client(HTTP_AUTHORIZATION="Bearer {}".format(api_key._api_key))
        response = c.get(reverse("wooey:wooey_home"))
        self.assertEqual(response.wsgi_request.user, api_key.profile.user)

    def test_fails_if_api_key_inactive(self):
        api_key = factories.APIKeyFactory(active=False)
        c = Client(HTTP_AUTHORIZATION="Bearer {}".format(api_key._api_key))
        response = c.get(reverse("wooey:wooey_home"))
        self.assertNotEqual(response.wsgi_request.user, api_key.profile.user)
