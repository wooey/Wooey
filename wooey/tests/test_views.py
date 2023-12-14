# TODO: Test for viewing a user's job as an anonymous user (fail case)

import json

from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.urls import reverse

from . import (
    config,
    factories,
    mixins,
    utils as test_utils,
)
from ..backend import utils
from ..views import wooey_celery
from .. import views as wooey_views
from .. import models
from .. import settings


User = get_user_model()


def load_JSON_dict(d):
    return json.loads(d.decode("utf-8"))


class CeleryViews(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    def setUp(self):
        super(CeleryViews, self).setUp()
        self.factory = RequestFactory()
        self.user = factories.UserFactory()
        # the test server doesn't have celery running
        settings.WOOEY_CELERY = False

    def test_celery_results(self):
        request = self.factory.get(reverse("wooey:all_queues_json"))
        request.user = self.user
        response = wooey_celery.all_queues_json(request)
        d = response.content.decode("utf-8")
        self.assertEqual(
            {
                "items": {"global": [], "results": [], "user": []},
                "totals": {"global": 0, "results": 0, "user": 0},
            },
            json.loads(d),
        )

        job = factories.generate_job(self.translate_script)
        job.save()
        response = wooey_celery.all_queues_json(request)
        d = json.loads(response.content.decode("utf-8"))
        self.assertEqual(1, d["totals"]["global"])

        job.user = self.user
        job.status = models.WooeyJob.RUNNING
        job.save()
        response = wooey_celery.all_queues_json(request)
        d = json.loads(response.content.decode("utf-8"))
        # we now are logged in, make sure the job appears under the user jobs
        self.assertEqual(1, d["totals"]["user"])

        user = AnonymousUser()
        request.user = user
        response = wooey_celery.all_queues_json(request)
        d = json.loads(response.content.decode("utf-8"))
        # test empty response since anonymous users should not see users jobs
        self.assertEqual(d["items"]["results"], [])
        self.assertEqual(d["items"]["user"], [])

    def test_celery_commands(self):
        job = factories.generate_job(self.translate_script)
        job.user = self.user
        job.save()
        celery_command = {"celery-command": ["delete"], "job-id": [job.pk]}
        # test that we cannot modify a users script
        request = self.factory.post(
            reverse("wooey:celery_task_command"), celery_command
        )
        anon = AnonymousUser()
        request.user = anon
        response = wooey_celery.celery_task_command(request)
        d = response.content.decode("utf-8")
        self.assertFalse(json.loads(d).get("valid"))

        # test a nonsense command
        celery_command.update({"celery-command": ["thisshouldfail"]})
        response = wooey_celery.celery_task_command(request)
        d = response.content.decode("utf-8")
        self.assertFalse(json.loads(d).get("valid"))

        # test that the user can interact with it
        # the stop command will break, so currently untested here until I figure it out
        for i in ["resubmit", "rerun", "delete"]:
            celery_command.update({"celery-command": [i]})
            request = self.factory.post(
                reverse("wooey:celery_task_command"),
                celery_command,
            )
            request.user = self.user
            response = wooey_celery.celery_task_command(request)
            d = response.content.decode("utf-8")
            self.assertTrue(json.loads(d).get("valid"))

    def test_celery_task_view(self):
        job = factories.generate_job(self.translate_script)
        job.user = self.user
        job.save()

        # test that an anonymous user cannot view a user's job
        view = wooey_celery.JobView.as_view()
        request = self.factory.get(
            reverse("wooey:celery_results", kwargs={"job_id": job.pk})
        )
        request.user = AnonymousUser()
        response = view(request, job_id=job.pk)
        response.render()
        self.assertIn("job_error", response.context_data)
        self.assertNotIn("job_info", response.context_data)

        # test the user can view the job
        request.user = self.user
        response = view(request, job_id=job.pk)
        response.render()
        self.assertNotIn("job_error", response.context_data)
        self.assertIn("job_info", response.context_data)

    def test_celery_nonexistent_task(self):
        # test request for non-existent job, should raise 404
        view = wooey_celery.JobView.as_view()
        request = self.factory.get(
            reverse("wooey:celery_results", kwargs={"job_id": "-1"})
        )
        with self.assertRaises(Http404):
            response = view(request, job_id=-1)
            response.render()


class WooeyViews(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    def setUp(self):
        super(WooeyViews, self).setUp()
        self.factory = RequestFactory()
        self.script_view_func = wooey_views.WooeyScriptView.as_view()
        self.json_view_func = wooey_views.WooeyScriptJSON.as_view()
        self.user = factories.UserFactory()
        # the test server doesn't have celery running
        settings.WOOEY_CELERY = False

    def test_multiple_choice_clone(self):
        from ..backend import utils

        script_version = self.choice_script
        script = script_version.script
        choices = ["2", "1", "3"]
        choice_param = "two_choices"
        job = utils.create_wooey_job(
            script_version_pk=script_version.pk,
            data={
                "job_name": "abc",
                choice_param: choices,
                "wooey_type": script_version.pk,
            },
        )
        request = self.factory.post(
            reverse(
                "wooey:wooey_script_clone",
                kwargs={"slug": job.script_version.script.slug, "job_id": job.pk},
            ),
            data={
                "wooey_type": script_version.pk,
            },
        )
        request.user = AnonymousUser()
        response = self.json_view_func(request, pk=script.pk, job_id=job.pk)
        self.assertEqual(response.status_code, 200)

    def test_clone_job_into_specific_version(self):
        # Test we can clone a job into a previous script's version

        # Create a job using version2
        job = factories.generate_job(self.version2_script)

        # Get a job using version 1
        job_kwargs = {
            "slug": self.version1_script.script.slug,
            "script_version": self.version1_script.script_version,
            "script_iteration": self.version1_script.script_iteration,
            "job_id": job.pk,
        }
        request = self.factory.get(
            reverse("wooey:wooey_script", kwargs=job_kwargs),
        )
        request.user = AnonymousUser()
        response = self.script_view_func(
            request, pk=self.version1_script.script.pk, **job_kwargs
        )
        self.assertEqual(response.status_code, 200)

        # Test that version1 was returned
        context = response.resolve_context(response.context_data)
        self.assertEqual(
            context["form"]["wooey_form"]["wooey_type"].value(), self.version1_script.pk
        )

    def test_multiple_choice(self):
        script_version = self.choice_script
        script = script_version.script
        two_choices_slug = test_utils.get_subparser_form_slug(
            script_version, "two_choices"
        )
        url = reverse("wooey:wooey_script", kwargs={"slug": script.slug})
        data = {
            "job_name": "abc",
            "wooey_type": script_version.pk,
            "wooey_parser": script_version.scriptparser_set.first().pk,
            two_choices_slug: ["2", "1", "3"],
        }
        filecount = 0
        for i, v in config.SCRIPT_DATA["choices"]["files"].items():
            slug = test_utils.get_subparser_form_slug(script_version, i)
            data[slug] = v
            filecount += len(v)
        request = self.factory.post(url, data=data)
        request.user = self.user
        response = self.json_view_func(request)
        d = load_JSON_dict(response.content)
        self.assertTrue(d["valid"], d)
        self.assertEqual(
            sum([len(request.FILES.getlist(i)) for i in request.FILES.keys()]),
            filecount,
        )

        # test submitting this in the 'currently' field
        job = models.WooeyJob.objects.latest("created_date")
        files = [
            i.value.name
            for i in job.get_parameters()
            if i.parameter.slug == "multiple_file_choices"
        ]

        data["multiple_file_choices"] = files
        request = self.factory.post(url, data=data)
        request.user = self.user
        response = self.json_view_func(request)
        self.assertEqual(response.status_code, 200)
        d = load_JSON_dict(response.content)
        self.assertTrue(d["valid"], d)

        # check the files are actually with the new model
        job = models.WooeyJob.objects.latest("created_date")
        new_files = [
            i.value.url
            for i in job.get_parameters()
            if i.parameter.slug == "multiple_file_choices"
        ]
        self.assertEqual(len(new_files), len(files))

    def test_form_groups(self):
        # Make sure forms groups work to validate
        script_version = self.without_args
        forms = utils.get_form_groups(script_version=self.without_args)
        data = {}
        data.update(config.SCRIPT_DATA["without_args"].get("data"))
        wooey_form = forms["wooey_form"]
        data.update(wooey_form.initial)
        subparser = list(forms["parsers"].keys())[0][0]
        data["wooey_parser"] = subparser

        url = reverse("wooey:wooey_script", kwargs={"slug": script_version.script.slug})
        request = self.factory.post(url, data=data)
        user = factories.UserFactory()
        request.user = user
        response = self.json_view_func(request)
        d = load_JSON_dict(response.content)
        self.assertTrue(d["valid"], d)

    def test_url_parameters_positional(self):
        script_version = self.command_order_script
        url = reverse("wooey:wooey_script", kwargs={"slug": script_version.script.slug})
        request = self.factory.get(
            url,
            data={
                "link": "abc",
            },
        )
        request.user = AnonymousUser()
        response = self.script_view_func(
            request,
            pk=script_version.script.pk,
        )
        self.assertEqual(response.status_code, 200)

        context = response.resolve_context(response.context_data)
        parser = list(context["form"]["parsers"].keys())[0]
        self.assertEqual(
            context["form"]["parsers"][parser][0]["form"]
            .fields[f"{parser[0]}-link"]
            .initial,
            "abc",
        )

    def test_url_parameters_optional(self):
        script_version = self.translate_script
        url = reverse("wooey:wooey_script", kwargs={"slug": script_version.script.slug})
        request = self.factory.get(
            url,
            data={
                "sequence": "abc",
            },
        )
        request.user = AnonymousUser()
        response = self.script_view_func(
            request,
            pk=script_version.script.pk,
        )
        self.assertEqual(response.status_code, 200)

        context = response.resolve_context(response.context_data)
        parser = list(context["form"]["parsers"].keys())[0]
        self.assertEqual(
            context["form"]["parsers"][parser][0]["form"]
            .fields[f"{parser[0]}-sequence"]
            .initial,
            "abc",
        )

    def test_url_parameters_multi_choice(self):
        script_version = self.choice_script
        url = reverse("wooey:wooey_script", kwargs={"slug": script_version.script.slug})
        request = self.factory.get(
            url,
            data={
                "one_choice": "0",
                "two_choices": ["0", "1"],
            },
        )
        request.user = AnonymousUser()
        response = self.script_view_func(
            request,
            pk=script_version.script.pk,
        )
        self.assertEqual(response.status_code, 200)

        context = response.resolve_context(response.context_data)
        parser = list(context["form"]["parsers"].keys())[0]
        self.assertEqual(
            context["form"]["parsers"][parser][1]["form"]
            .fields[f"{parser[0]}-one_choice"]
            .initial,
            "0",
        )
        self.assertEqual(
            context["form"]["parsers"][parser][1]["form"]
            .fields[f"{parser[0]}-two_choices"]
            .initial,
            ["0", "1"],
        )

    def test_url_parameters_subparser(self):
        script_version = self.subparser_script
        url = reverse("wooey:wooey_script", kwargs={"slug": script_version.script.slug})
        request = self.factory.get(url, data={"test_arg": "3.3", "sp1": "2"})
        request.user = AnonymousUser()
        response = self.script_view_func(
            request,
            pk=script_version.script.pk,
        )
        self.assertEqual(response.status_code, 200)

        context = response.resolve_context(response.context_data)
        main_parser, subparser1, subparser2 = list(context["form"]["parsers"].keys())
        self.assertEqual(
            context["form"]["parsers"][main_parser][0]["form"]
            .fields[f"{main_parser[0]}-test_arg"]
            .initial,
            "3.3",
        )
        self.assertEqual(
            context["form"]["parsers"][subparser1][0]["form"]
            .fields[f"{subparser1[0]}-sp1"]
            .initial,
            "2",
        )

    def test_job_view_permissions(self):
        # Make sure users cannot see jobs from other users
        job = factories.generate_job(self.translate_script)
        url = reverse("wooey:celery_results", kwargs={"job_id": job.pk})

        # Make a new user
        user1 = User(username="wooey")
        user1.save()
        user2 = User(username="wooey2")
        user2.save()
        request = self.factory.get(url)
        request.user = user1
        view = wooey_celery.JobView.as_view()
        response = view(request, job_id=job.pk)
        self.assertEqual(response.status_code, 200)

        job.user = user2
        job.save()

        response = view(request, job_id=job.pk)
        response.render()
        self.assertContains(
            response, models.WooeyJob.error_messages["invalid_permissions"]
        )

    def test_validates_chosen_subparser(self):
        # Addresses https://github.com/wooey/Wooey/issues/288
        script_version = self.subparser_script
        script = script_version.script
        sp2_slug = test_utils.get_subparser_form_slug(script_version, "sp2")
        subparser = script_version.scriptparser_set.get(name="subparser2")
        url = reverse("wooey:wooey_script", kwargs={"slug": script.slug})
        data = {
            "job_name": "abc",
            "wooey_type": script_version.pk,
            "wooey_parser": subparser.pk,
            sp2_slug: [1],
        }
        request = self.factory.post(url, data=data)
        request.user = self.user
        response = self.json_view_func(request)
        d = load_JSON_dict(response.content)
        self.assertTrue(d["valid"], d)

    def test_fails_if_required_subparser_argument_not_used(self):
        # Addresses https://github.com/wooey/Wooey/issues/288
        script_version = self.subparser_script
        script = script_version.script
        subparser = script_version.scriptparser_set.get(name="subparser2")
        url = reverse("wooey:wooey_script", kwargs={"slug": script.slug})
        data = {
            "job_name": "abc",
            "wooey_type": script_version.pk,
            "wooey_parser": subparser.pk,
        }
        request = self.factory.post(url, data=data)
        request.user = self.user
        response = self.json_view_func(request)
        d = load_JSON_dict(response.content)
        self.assertFalse(d["valid"], d)


class WoeeyScriptSearchViews(
    mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase
):
    def setUp(self):
        super(WoeeyScriptSearchViews, self).setUp()
        self.factory = RequestFactory()
        self.json_view_func = wooey_views.WooeyScriptSearchJSON.as_view()
        self.json_html_view_func = wooey_views.WooeyScriptSearchJSONHTML.as_view()
        # the test server doesn't have celery running
        settings.WOOEY_CELERY = False

        self.script1 = factories.ScriptFactory(
            script_name="test script 1 name",
            script_description="test script 1 description",
        )
        self.script2 = factories.ScriptFactory(
            script_name="test script 2 name",
            script_description="test script 2 description",
        )

    def test_search_json_with_name(self):
        url = reverse("wooey:wooey_search_script_json")
        request = self.factory.get(url, data={"q": "1 name"})
        response = self.json_view_func(request)
        d = load_JSON_dict(response.content)
        self.assertEqual(len(d["results"]), 1)
        self.assertEqual(
            set(result["id"] for result in d["results"]), {self.script1.id}
        )

    def test_search_json_with_description(self):
        url = reverse("wooey:wooey_search_script_json")
        request = self.factory.get(url, data={"q": "2 description"})
        response = self.json_view_func(request)
        d = load_JSON_dict(response.content)
        self.assertEqual(len(d["results"]), 1)
        self.assertEqual(
            set(result["id"] for result in d["results"]), {self.script2.id}
        )

    def test_search_json_html_with_name(self):
        url = reverse("wooey:wooey_search_script_jsonhtml")
        request = self.factory.get(url, data={"q": "1 name"})
        response = self.json_view_func(request)
        d = load_JSON_dict(response.content)
        self.assertEqual(len(d["results"]), 1)
        self.assertEqual(
            set(result["id"] for result in d["results"]), {self.script1.id}
        )

    def test_search_json_html_with_description(self):
        url = reverse("wooey:wooey_search_script_jsonhtml")
        request = self.factory.get(url, data={"q": "2 description"})
        response = self.json_view_func(request)
        d = load_JSON_dict(response.content)
        self.assertEqual(len(d["results"]), 1)
        self.assertEqual(
            set(result["id"] for result in d["results"]), {self.script2.id}
        )


class TestApiKeyViews(TestCase):
    def setUp(self):
        self.request = RequestFactory()

    def test_can_create_api_key(self):
        url = reverse("wooey:create_api_key")
        request = self.request.post(url, data={"name": "test-key"})
        request.user = factories.UserFactory()
        response = wooey_views.create_api_key(request)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["name"], "test-key")
        self.assertIn("api_key", data)

    def test_can_toggle_api_key(self):
        api_key = factories.APIKeyFactory()
        self.assertTrue(api_key.active)
        url = reverse("wooey:toggle_api_key", kwargs={"id": api_key.id})
        request = self.request.post(url)
        request.user = factories.UserFactory()
        response = wooey_views.toggle_api_key(request, id=api_key.id)
        api_key.refresh_from_db()
        self.assertFalse(api_key.active)
        response = wooey_views.toggle_api_key(request, id=api_key.id)
        api_key.refresh_from_db()
        self.assertTrue(api_key.active)

    def test_cant_toggle_api_key_if_wrong_user(self):
        api_key = factories.APIKeyFactory()
        self.assertTrue(api_key.active)
        url = reverse("wooey:toggle_api_key", kwargs={"id": api_key.id})
        request = self.request.post(url)
        new_profile = factories.ProfileFactory(user__username="foo")
        request.user = new_profile.user
        response = wooey_views.toggle_api_key(request, id=api_key.id)
        self.assertEqual(response.status_code, 404)

    def test_cant_delete_api_key_if_wrong_user(self):
        api_key = factories.APIKeyFactory()
        self.assertEqual(models.APIKey.objects.filter(pk=api_key.id).count(), 1)
        url = reverse("wooey:delete_api_key", kwargs={"id": api_key.id})
        request = self.request.delete(url)
        new_profile = factories.ProfileFactory(user__username="foo")
        request.user = new_profile.user
        response = wooey_views.delete_api_key(request, id=api_key.id)
        self.assertEqual(response.status_code, 404)


class TestProfileView(TestCase):
    def test_doesnt_show_settings_if_not_logged_in_user(self):
        request_factory = RequestFactory()
        other_user = factories.UserFactory(username="someone-else")
        user = factories.UserFactory()
        url = reverse("wooey:profile", kwargs={"username": user.username})

        request = request_factory.get(url)
        request.user = other_user
        view = wooey_views.WooeyProfileView.as_view()
        response = view(request, username=user.username)
        self.assertFalse(response.context_data["is_logged_in_user"])

    def test_show_settings_if_logged_in_user(self):
        request_factory = RequestFactory()
        factories.UserFactory(username="someone-else")
        user = factories.UserFactory()
        url = reverse("wooey:profile", kwargs={"username": user.username})

        request = request_factory.get(url)
        request.user = user
        view = wooey_views.WooeyProfileView.as_view()
        response = view(request, username=user.username)
        self.assertTrue(response.context_data["is_logged_in_user"])


class TestHomeView(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):
    def test_sorts_scripts_by_name_and_favorite(self):
        request_factory = RequestFactory()
        user = factories.UserFactory()
        url = reverse("wooey:wooey_home")
        request = request_factory.get(url)
        request.user = user

        # by default, we sort by name
        view = wooey_views.WooeyHomeView.as_view()
        response = view(request)

        sorted_scripts = sorted(
            models.Script.objects.all(), key=lambda x: x.script_name
        )
        self.assertEqual(response.context_data["scripts"], sorted_scripts)

        ctype = ContentType.objects.get_for_model(models.Script)
        models.Favorite(
            content_type=ctype, user=user, object_id=self.translate_script.script.id
        ).save()

        # assert this script isn't naturally the first one
        self.assertNotEqual(sorted_scripts[0].id, self.translate_script.script.id)

        view = wooey_views.WooeyHomeView.as_view()
        response = view(request)

        self.assertTrue(
            response.context_data["scripts"][0].id, self.translate_script.script.id
        )

        # the rest after the favorite are sorted alphabetically
        self.assertEqual(
            response.context_data["scripts"][1:],
            [i for i in sorted_scripts if i.id != self.translate_script.script.id],
        )
