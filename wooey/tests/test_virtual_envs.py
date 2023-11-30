import os
import shutil
import subprocess
from unittest import mock

from django.test import TransactionTestCase

from wooey import settings as wooey_settings
from wooey.backend.utils import create_wooey_job
from wooey.models import WooeyJob
from wooey.tasks import setup_venv

from . import config
from .factories import VirtualEnvFactory, generate_script


class TestVirtualEnvironments(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.venv = VirtualEnvFactory()
        install_path = self.venv.get_install_path()
        if os.path.exists(install_path):
            shutil.rmtree(install_path)

    def test_sets_up_virtual_env(self):
        venv = self.venv
        (venv_executable, stdout, stderr, return_code) = setup_venv(venv)
        self.assertTrue(os.path.exists(venv_executable))

    def test_reuses_virtual_env(self):
        venv = self.venv
        (venv_executable, stdout, stderr, return_code) = setup_venv(venv)
        self.assertTrue(os.path.exists(venv_executable))
        with mock.patch("wooey.tasks.run_and_stream_command") as command_runner:
            command_runner.return_value = ("stdout", "stderr", 0)
            setup_venv(venv)
            self.assertFalse(command_runner.called)

    def test_installs_pip(self):
        venv = self.venv
        setup_venv(venv)
        if wooey_settings.IS_WINDOWS:
            self.assertTrue(
                os.path.exists(
                    os.path.join(venv.get_install_path(), "Scripts", "pip.exe")
                )
            )
        else:
            self.assertTrue(
                os.path.exists(os.path.join(venv.get_install_path(), "bin", "pip"))
            )

    def test_installs_requirements(self):
        venv = self.venv
        venv.requirements = "flask"
        venv.save()
        setup_venv(venv)
        binary = venv.get_venv_python_binary()
        results = subprocess.run(
            [binary, "-m" "pip", "freeze", "--local"], capture_output=True
        )
        packages = results.stdout.decode().lower()
        self.assertIn("flask", packages)

    def test_job_can_run_in_venv(self):
        # For this, we install a package that is only in the venv (pandas) and make sure it runs
        pandas_script_path = os.path.join(
            config.WOOEY_TEST_SCRIPTS, "venv_pandas_test.py"
        )
        pandas_script_version = generate_script(
            pandas_script_path,
            script_name="pandas-test",
            ignore_bad_imports=True,
        )
        pandas_script = pandas_script_version.script
        venv = self.venv
        venv.requirements = "pandas"
        venv.save()
        pandas_script.virtual_environment = venv
        pandas_script.save()
        job = create_wooey_job(
            script_version_pk=pandas_script_version.pk,
            data={
                "job_name": "abc",
            },
        )
        self.assertEqual(job.status, WooeyJob.SUBMITTED)
        job = job.submit_to_celery()
        job.refresh_from_db()
        self.assertEqual(job.status, WooeyJob.COMPLETED)
