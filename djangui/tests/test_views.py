import json

from django.test import TestCase, RequestFactory
from django.core.urlresolvers import reverse

from . import factories, mixins
from ..views import djangui_celery

class CeleryViews(mixins.ScriptFactoryMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_celery_results(self):
        request = self.factory.get(reverse('celery_results'))
        user = factories.UserFactory()
        request.user = user
        response = djangui_celery.celery_status(request)
        d = response.content.decode("utf-8")
        self.assertEqual({'anon': [], 'user': []}, json.loads(d))
        job = factories.JobFactory()
        job.save()
        response = djangui_celery.celery_status(request)
        d = json.loads(response.content.decode("utf-8"))
        self.assertEqual(1, len(d['anon']))
        job.user = user
        job.save()
        response = djangui_celery.celery_status(request)
        d = json.loads(response.content.decode("utf-8"))
        # we now are logged in, make sure the job appears under the user jobs
        self.assertEqual(1, len(d['user']))
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
        request.user = user
        response = djangui_celery.celery_status(request)
        d = json.loads(response.content.decode("utf-8"))
        # test empty response since anonymous users should not see users jobs
        self.assertEqual({'anon': [], 'user': []}, d)