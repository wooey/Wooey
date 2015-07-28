# TODO: Test for viewing a user's job as an anonymous user (fail case)

import json

from django.test import TestCase, RequestFactory, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser

from . import factories, mixins, config
from ..views import wooey_celery
from .. import views as wooey_views

class CeleryViews(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_celery_results(self):
        request = self.factory.get(reverse('wooey:celery_results'))
        user = factories.UserFactory()
        request.user = user
        response = wooey_celery.celery_status(request)
        d = response.content.decode("utf-8")
        self.assertEqual({'anon': [], 'user': []}, json.loads(d))
        job = factories.TranslateJobFactory()
        job.save()
        response = wooey_celery.celery_status(request)
        d = json.loads(response.content.decode("utf-8"))
        self.assertEqual(1, len(d['anon']))
        job.user = user
        job.save()
        response = wooey_celery.celery_status(request)
        d = json.loads(response.content.decode("utf-8"))
        # we now are logged in, make sure the job appears under the user jobs
        self.assertEqual(1, len(d['user']))
        user = AnonymousUser()
        request.user = user
        response = wooey_celery.celery_status(request)
        d = json.loads(response.content.decode("utf-8"))
        # test empty response since anonymous users should not see users jobs
        self.assertEqual({'anon': [], 'user': []}, d)

    def test_celery_commands(self):
        user = factories.UserFactory()
        job = factories.TranslateJobFactory()
        job.user = user
        job.save()
        celery_command = {'celery-command': ['delete'], 'job-id': [job.pk]}
        # test that we cannot modify a users script
        request = self.factory.post(reverse('wooey:celery_task_command'),
                                    celery_command)
        anon = AnonymousUser()
        request.user = anon
        response = wooey_celery.celery_task_command(request)
        d = response.content.decode("utf-8")
        self.assertFalse(json.loads(d).get('valid'))

        # test a nonsense command
        celery_command.update({'celery-command': ['thisshouldfail']})
        response = wooey_celery.celery_task_command(request)
        d = response.content.decode("utf-8")
        self.assertFalse(json.loads(d).get('valid'))

        # test that the user can interact with it
        for i in ['resubmit', 'rerun', 'clone', 'stop', 'delete']:
            celery_command.update({'celery-command': [i]})
            request = self.factory.post(reverse('wooey:celery_task_command'),
                                    celery_command)
            request.user = user
            response = wooey_celery.celery_task_command(request)
            d = response.content.decode("utf-8")
            self.assertTrue(json.loads(d).get('valid'))

    def test_celery_task_view(self):
        user = factories.UserFactory()
        job = factories.TranslateJobFactory()
        job.user = user
        job.save()
        # test that an anonymous user cannot view a user's job
        view = wooey_celery.CeleryTaskView.as_view()
        request = self.factory.get(reverse('wooey:celery_results_info', kwargs={'job_id': job.pk}))
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
        request = self.factory.get(reverse('wooey:celery_results_info', kwargs={'job_id': '-1'}))
        response = view(request, job_id=-1)
        self.assertIn('task_error', response.context_data)
        self.assertNotIn('task_info', response.context_data)

class WooeyViews(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.script_view_func = wooey_views.WooeyScriptJSON.as_view()

    def test_multiple_choice_clone(self):
        from ..backend import utils
        script = factories.ChoiceScriptFactory()
        choices = ['2', '1', '3']
        choice_param = 'two_choices'
        job = utils.create_wooey_job(script_pk=script.pk, data={'job_name': 'abc', choice_param: choices})
        request = self.factory.get(reverse('wooey:wooey_script_clone',
                                           kwargs={'script_group': job.script.script_group.slug, 'script_name': job.script.slug, 'job_id': job.pk}))
        response = self.script_view_func(request, pk=job.pk, job_id=job.pk)
        self.assertEqual(response.status_code, 200)

    def test_multiple_choice(self):
        script = factories.ChoiceScriptFactory()
        url = reverse('wooey:wooey_script', kwargs={'script_group': script.script_group.slug, 'script_name': script.slug})
        data = {'job_name': 'abc', 'wooey_type': script.pk, 'two_choices': ['2', '1', '3']}
        filecount = 0
        for i,v in config.SCRIPT_DATA['choices']['files'].items():
            data[i] = v
            filecount += len(v)
        request = self.factory.post(url, data=data)
        request.user = AnonymousUser()
        response = self.script_view_func(request)
        self.assertTrue(json.loads(response.content)['valid'])
        self.assertEqual(sum([len(request.FILES.getlist(i)) for i in request.FILES.keys()]), filecount)

        # test submitting this in the 'currently' field
        from ..models import WooeyJob
        job = WooeyJob.objects.latest('created_date')
        files = [i.value.path for i in job.get_parameters() if i.parameter.slug == 'multiple_file_choices']

        data['multiple_file_choices'] = files
        request = self.factory.post(url, data=data)
        request.user = AnonymousUser()
        response = self.script_view_func(request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json.loads(response.content)['valid'])

        # check the files are actually with the new model
        job = WooeyJob.objects.latest('created_date')
        new_files = [i.value.url for i in job.get_parameters() if i.parameter.slug == 'multiple_file_choices']
        self.assertEqual(len(new_files), len(files))