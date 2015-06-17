# TODO: Test for viewing a user's job as an anonymous user (fail case)

import json

from django.test import TestCase, RequestFactory, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser

from . import factories, mixins
from ..views import djangui_celery

class CeleryViews(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_celery_results(self):
        request = self.factory.get(reverse('djangui:celery_results'))
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
        user = AnonymousUser()
        request.user = user
        response = djangui_celery.celery_status(request)
        d = json.loads(response.content.decode("utf-8"))
        # test empty response since anonymous users should not see users jobs
        self.assertEqual({'anon': [], 'user': []}, d)

    def test_celery_commands(self):
        user = factories.UserFactory()
        job = factories.JobFactory()
        job.user = user
        job.save()
        celery_command = {'celery-command': ['delete'], 'job-id': [job.pk]}
        # test that we cannot modify a users script
        request = self.factory.post(reverse('djangui:celery_task_command'),
                                    celery_command)
        anon = AnonymousUser()
        request.user = anon
        response = djangui_celery.celery_task_command(request)
        d = response.content.decode("utf-8")
        self.assertFalse(json.loads(d).get('valid'))

        # test a nonsense command
        celery_command.update({'celery-command': ['thisshouldfail']})
        response = djangui_celery.celery_task_command(request)
        d = response.content.decode("utf-8")
        self.assertFalse(json.loads(d).get('valid'))

        # test that the user can interact with it
        request.user = user
        for i in ['resubmit', 'rerun', 'clone', 'stop', 'delete']:
            celery_command.update({'celery-command': [i]})
            response = djangui_celery.celery_task_command(request)
            d = response.content.decode("utf-8")
            self.assertTrue(json.loads(d).get('valid'))

    def test_celery_task_view(self):
        user = factories.UserFactory()
        job = factories.JobFactory()
        job.user = user
        job.save()
        # test that an anonymous user cannot view a user's job
        view = djangui_celery.CeleryTaskView.as_view()
        request = self.factory.get(reverse('djangui:celery_results_info', kwargs={'job_id': job.pk}))
        request.user = AnonymousUser()
        response = view(request, job_id=job.pk)
        self.assertIn('task_error', response.context_data)
        self.assertNotIn('task_info', response.context_data)

        # test the user can view the job
        request.user = user
        response = view(request, job_id=job.pk)
        self.assertNotIn('task_error', response.context_data)
        self.assertIn('task_info', response.context_data)

        # test that jobs that don't exist don't fail horridly
        request = self.factory.get(reverse('djangui:celery_results_info', kwargs={'job_id': '-1'}))
        response = view(request, job_id=-1)
        self.assertIn('task_error', response.context_data)
        self.assertNotIn('task_info', response.context_data)