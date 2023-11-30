import os
import shutil
import subprocess
from unittest import mock

from django.test import TestCase

from wooey.tasks import setup_venv

from .factories import VirtualEnvFactory


class TestVirtualEnvironments(TestCase):
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
