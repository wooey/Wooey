import os
from io import BytesIO

from django.test import Client, TransactionTestCase
from django.urls import reverse

from ..models import WooeyJob

from . import mixins, factories


class ApiTestMixin(object):
    def setUp(self):
        api_key = factories.APIKeyFactory()
        self.client = Client(HTTP_AUTHORIZATION="Bearer {}".format(api_key._api_key))
        return super().setUp()


class TestJobStatus(mixins.ScriptFactoryMixin, ApiTestMixin, TransactionTestCase):
    def test_reports_when_job_is_complete(self):
        job = factories.generate_job(self.translate_script)
        response = self.client.get(
            reverse("wooey:api_job_status", kwargs={"job_id": job.id})
        )
        self.assertFalse(response.json()["is_complete"])
        job.status = WooeyJob.COMPLETED
        job.save()
        response = self.client.get(
            reverse("wooey:api_job_status", kwargs={"job_id": job.id})
        )
        self.assertTrue(response.json()["is_complete"])

    def test_error_when_invalid_user(self):
        another_user = factories.UserFactory(username="bob")
        job = factories.generate_job(self.translate_script)
        job.user = another_user
        job.save()
        response = self.client.get(
            reverse("wooey:api_job_status", kwargs={"job_id": job.id})
        )
        self.assertFalse(response.json()["valid"])
        self.assertEqual(response.status_code, 403)


class TestJobDetails(
    mixins.ScriptFactoryMixin,
    mixins.FileCleanupMixin,
    ApiTestMixin,
    TransactionTestCase,
):
    def test_job_details(self):
        job = self.create_job_with_output_files()
        response = self.client.get(
            reverse("wooey:api_job_details", kwargs={"job_id": job.id})
        )
        data = response.json()
        self.assertIn("url", data["assets"][0])
        self.assertTrue(data["is_complete"])
        self.assertEqual(job.job_name, data["job_name"])


class TestScriptAddition(mixins.ScriptFactoryMixin, ApiTestMixin, TransactionTestCase):
    def test_can_add_new_scripts(self):
        payload = {
            "group": "test group",
            "translate-script": open(self.translate_script_path, "rb"),
            "choice-script": open(self.choice_script_path, "rb"),
        }
        response = self.client.post(
            reverse("wooey:api_add_or_update_script"),
            data=payload,
        )
        data = response.json()
        self.assertEqual(data[0]["script"], "translate-script")
        self.assertEqual(data[1]["script"], "choice-script")

    def test_can_update_existing_script(self):
        payload = {
            "group": "test group",
            "update-script": open(self.version1_script_path, "rb"),
        }
        response = self.client.post(
            reverse("wooey:api_add_or_update_script"),
            data=payload,
        )
        data = response.json()
        self.assertEqual(data[0]["script"], "update-script")
        self.assertEqual(data[0]["iteration"], 1)
        self.assertEqual(data[0]["version"], "1")
        payload = {
            "group": "test group",
            "update-script": open(self.version2_script_path, "rb"),
        }
        response = self.client.post(
            reverse("wooey:api_add_or_update_script"),
            data=payload,
        )
        data = response.json()
        self.assertEqual(data[0]["script"], "update-script")
        self.assertEqual(data[0]["version"], "1")
        self.assertEqual(data[0]["iteration"], 2)
        self.assertEqual(data[0]["is_default"], True)

    def test_can_disable_default_update(self):
        payload = {
            "group": "test group 2",
            "update-script": open(self.version1_script_path, "rb"),
        }
        response = self.client.post(
            reverse("wooey:api_add_or_update_script"),
            data=payload,
        )
        data = response.json()
        self.assertEqual(data[0]["script"], "update-script")
        self.assertEqual(data[0]["iteration"], 1)
        self.assertEqual(data[0]["version"], "1")
        payload = {
            "group": "test group 2",
            "default": False,
            "update-script": open(self.version2_script_path, "rb"),
        }
        response = self.client.post(
            reverse("wooey:api_add_or_update_script"),
            data=payload,
        )
        data = response.json()
        self.assertEqual(data[0]["script"], "update-script")
        self.assertEqual(data[0]["version"], "1")
        self.assertEqual(data[0]["iteration"], 2)
        self.assertEqual(data[0]["is_default"], False)


class TestScriptSubmission(
    mixins.ScriptFactoryMixin, ApiTestMixin, TransactionTestCase
):
    def test_defaults_to_latest_script(self):
        payload = {
            "group": "test group 2",
            "update-script": open(self.version1_script_path, "rb"),
        }
        response = self.client.post(
            reverse("wooey:api_add_or_update_script"),
            data=payload,
        )
        payload = {
            "group": "test group 2",
            "update-script": open(self.version2_script_path, "rb"),
        }
        response = self.client.post(
            reverse("wooey:api_add_or_update_script"),
            data=payload,
        )
        payload = {
            "job_name": "test",
            "command": "--one 1 --two 2",
        }
        response = self.client.post(
            reverse("wooey:api_submit_script", kwargs={"slug": "update-script"}),
            data=payload,
            content_type="application/json",
        )
        data = response.json()
        self.assertTrue(data["valid"])
        job = WooeyJob.objects.get(id=data["job_id"])
        self.assertEqual(job.script_version.script_iteration, 2)

    def test_can_specify_version(self):
        payload = {
            "group": "test group 2",
            "update-script": open(self.version1_script_path, "rb"),
        }
        response = self.client.post(
            reverse("wooey:api_add_or_update_script"),
            data=payload,
        )
        payload = {
            "group": "test group 2",
            "update-script": open(self.version2_script_path, "rb"),
        }
        response = self.client.post(
            reverse("wooey:api_add_or_update_script"),
            data=payload,
        )
        payload = {
            "job_name": "test",
            "iteration": 1,
            "command": "--one 1",
        }
        response = self.client.post(
            reverse("wooey:api_submit_script", kwargs={"slug": "update-script"}),
            data=payload,
            content_type="application/json",
        )
        data = response.json()
        self.assertTrue(data["valid"])
        job = WooeyJob.objects.get(id=data["job_id"])
        self.assertEqual(job.script_version.script_iteration, 1)

    def test_can_submit_script_with_json(self):
        script_version = self.translate_script
        payload = {
            "job_name": "test",
            "job_description": "a test job",
            "command": "--sequence aaa",
        }
        response = self.client.post(
            reverse(
                "wooey:api_submit_script", kwargs={"slug": script_version.script.slug}
            ),
            data=payload,
            content_type="application/json",
        )
        data = response.json()
        self.assertTrue(data["valid"])
        job = WooeyJob.objects.get(id=data["job_id"])
        self.assertEqual(job.job_description, "a test job")
        self.assertEqual(
            job.scriptparameters_set.get(parameter__slug="sequence").value, "aaa"
        )

    def test_submit_script_with_mixed_form_data(self):
        script_version = self.translate_script
        contents = b">test sequence\naaaggg\n"
        fasta_file = BytesIO(contents)
        payload = {
            "job_name": "test",
            "command": "--fasta fasta",
            "fasta": fasta_file,
        }
        response = self.client.post(
            reverse(
                "wooey:api_submit_script", kwargs={"slug": script_version.script.slug}
            ),
            data=payload,
        )
        data = response.json()
        self.assertTrue(data["valid"])
        job = WooeyJob.objects.get(id=data["job_id"])
        self.assertEqual(
            job.scriptparameters_set.get(parameter__slug="fasta").value.read(), contents
        )

    def test_submit_multiple_files_and_inputs(self):
        script_version = self.choice_script
        contents1 = b"foo"
        contents2 = b"bar"
        file1 = BytesIO(contents1)
        file2 = BytesIO(contents2)
        payload = {
            "job_name": "test",
            "command": "--need-at-least-one-numbers 1 2 3 --multiple-file-choices file1 file2",
            "file1": file1,
            "file2": file2,
        }
        response = self.client.post(
            reverse(
                "wooey:api_submit_script", kwargs={"slug": script_version.script.slug}
            ),
            data=payload,
        )
        data = response.json()
        self.assertTrue(data["valid"])
        job = WooeyJob.objects.get(id=data["job_id"])
        uploaded_files = {
            os.path.basename(i.value.name): i.value
            for i in job.scriptparameters_set.filter(
                parameter__slug="multiple_file_choices"
            )
        }
        self.assertEqual(len(uploaded_files), 2)
        self.assertEqual(uploaded_files["file1"].read(), contents1)
        self.assertEqual(uploaded_files["file2"].read(), contents2)
        self.assertEqual(
            sorted(
                [
                    i.value
                    for i in job.scriptparameters_set.filter(
                        parameter__slug="need_at_least_one_numbers"
                    ).all()
                ]
            ),
            [1, 2, 3],
        )
