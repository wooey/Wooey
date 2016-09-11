# TODO: Test for viewing a user's job as an anonymous user (fail case)

import json
from itertools import chain

from django.test import TestCase, RequestFactory, Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser
from django.http import Http404

from nose.tools import raises

from . import factories, mixins, config
from ..backend import utils
from ..views import wooey_celery
from .. import views as wooey_views
from .. import settings


def load_JSON_dict(d):
    return json.loads(d.decode('utf-8'))


class CeleryViews(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    def setUp(self):
        super(CeleryViews, self).setUp()
        self.factory = RequestFactory()
        # the test server doesn't have celery running
        settings.WOOEY_CELERY = False

    def test_celery_results(self):
        request = self.factory.get(reverse('wooey:all_queues_json'))
        user = factories.UserFactory()
        request.user = user
        response = wooey_celery.all_queues_json(request)
        d = response.content.decode("utf-8")
        self.assertEqual({u'items': {u'global': [], u'results': [], u'user': []},
                          u'totals': {u'global': 0, u'results': 0, u'user': 0}
                            }, json.loads(d))

        job = factories.generate_job(self.translate_script)
        job.save()
        response = wooey_celery.all_queues_json(request)
        d = json.loads(response.content.decode("utf-8"))
        self.assertEqual(1, d['totals']['global'])

        job.user = user
        job.save()
        response = wooey_celery.all_queues_json(request)
        d = json.loads(response.content.decode("utf-8"))
        # we now are logged in, make sure the job appears under the user jobs
        self.assertEqual(1, d['totals']['user'])

        user = AnonymousUser()
        request.user = user
        response = wooey_celery.all_queues_json(request)
        d = json.loads(response.content.decode("utf-8"))
        # test empty response since anonymous users should not see users jobs
        self.assertEqual(d['items']['results'], [])
        self.assertEqual(d['items']['user'], [])

    def test_celery_commands(self):
        user = factories.UserFactory()
        job = factories.generate_job(self.translate_script)
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
        # the stop command will break, so currently untested here until I figure it out
        for i in ['resubmit', 'rerun', 'clone', 'delete']:
            celery_command.update({'celery-command': [i]})
            request = self.factory.post(reverse('wooey:celery_task_command'),
                                    celery_command)
            request.user = user
            response = wooey_celery.celery_task_command(request)
            d = response.content.decode("utf-8")
            self.assertTrue(json.loads(d).get('valid'))

    def test_celery_task_view(self):
        user = factories.UserFactory()
        job = factories.generate_job(self.translate_script)
        job.user = user
        job.save()

        # test that an anonymous user cannot view a user's job
        view = wooey_celery.JobView.as_view()
        request = self.factory.get(reverse('wooey:celery_results', kwargs={'job_id': job.pk}))
        request.user = AnonymousUser()
        response = view(request, job_id=job.pk)
        self.assertIn('job_error', response.context_data)
        self.assertNotIn('job_info', response.context_data)

        # test the user can view the job
        request.user = user
        response = view(request, job_id=job.pk)
        self.assertNotIn('job_error', response.context_data)
        self.assertIn('job_info', response.context_data)

    @raises(Http404)
    def test_celery_nonexistent_task(self):
        # test request for non-existent job, should raise 404
        view = wooey_celery.JobView.as_view()
        request = self.factory.get(reverse('wooey:celery_results', kwargs={'job_id': '-1'}))
        response = view(request, job_id=-1)


class WooeyViews(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    def setUp(self):
        super(WooeyViews, self).setUp()
        self.factory = RequestFactory()
        self.script_view_func = wooey_views.WooeyScriptJSON.as_view()
        # the test server doesn't have celery running
        settings.WOOEY_CELERY = False

    def test_multiple_choice_clone(self):
        from ..backend import utils
        script_version = self.choice_script
        script = script_version.script
        choices = ['2', '1', '3']
        choice_param = 'two_choices'
        job = utils.create_wooey_job(script_version_pk=script_version.pk, data={'job_name': 'abc', choice_param: choices, 'wooey_type': script_version.pk})
        request = self.factory.post(reverse('wooey:wooey_script_clone',
                                           kwargs={'slug': job.script_version.script.slug, 'job_id': job.pk}),
                                    data={'wooey_type': script_version.pk})
        request.user = AnonymousUser()
        response = self.script_view_func(request, pk=job.pk, job_id=job.pk)
        self.assertEqual(response.status_code, 200)

    def test_multiple_choice(self):
        user = factories.UserFactory()
        script_version = self.choice_script
        script = script_version.script
        url = reverse('wooey:wooey_script', kwargs={'slug': script.slug})
        data = {'job_name': 'abc', 'wooey_type': script_version.pk, 'two_choices': ['2', '1', '3']}
        filecount = 0
        for i, v in config.SCRIPT_DATA['choices']['files'].items():
            data[i] = v
            filecount += len(v)
        request = self.factory.post(url, data=data)
        request.user = user
        response = self.script_view_func(request)
        d = load_JSON_dict(response.content)
        self.assertTrue(d['valid'], d)
        self.assertEqual(sum([len(request.FILES.getlist(i)) for i in request.FILES.keys()]), filecount)

        # test submitting this in the 'currently' field
        from ..models import WooeyJob
        job = WooeyJob.objects.latest('created_date')
        files = [i.value.name for i in job.get_parameters() if i.parameter.slug == 'multiple_file_choices']

        data['multiple_file_choices'] = files
        request = self.factory.post(url, data=data)
        request.user = user
        response = self.script_view_func(request)
        self.assertEqual(response.status_code, 200)
        d = load_JSON_dict(response.content)
        self.assertTrue(d['valid'], d)

        # check the files are actually with the new model
        job = WooeyJob.objects.latest('created_date')
        new_files = [i.value.url for i in job.get_parameters() if i.parameter.slug == 'multiple_file_choices']
        self.assertEqual(len(new_files), len(files))


    def test_form_groups(self):
        # Make sure forms groups work to validate
        script_version = self.without_args
        forms = utils.get_form_groups(script_version=self.without_args)
        data = {}
        for form in chain(forms['groups'], [forms['wooey_form']]):
            initial = form.initial
            initial.update(config.SCRIPT_DATA['without_args'].get('data'))
            data.update(initial)

        url = reverse('wooey:wooey_script', kwargs={'slug': script_version.script.slug})
        request = self.factory.post(url, data=data)
        user = factories.UserFactory()
        request.user = user
        response = self.script_view_func(request)
        d = load_JSON_dict(response.content)
        self.assertTrue(d['valid'], d)
