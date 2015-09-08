__author__ = 'chris'
from unittest import TestCase
import subprocess
import os
import shutil
import sys

BASE_DIR = os.path.split(__file__)[0]
WOOEY_SCRIPT_PATH = os.path.join(BASE_DIR, '..', 'scripts', 'wooify')
WOOEY_TEST_PROJECT_NAME = 'wooey_project'
WOOEY_TEST_PROJECT_PATH = os.path.join(BASE_DIR, WOOEY_TEST_PROJECT_NAME)
WOOEY_TEST_PROJECT_MANAGE = os.path.join(WOOEY_TEST_PROJECT_PATH, 'manage.py')
PYTHON_INTERPRETTER = sys.executable if sys.executable else 'python'

env = os.environ
env['DJANGO_SETTINGS_MODULE'] = '{}.settings'.format(WOOEY_TEST_PROJECT_NAME)
env['TESTING'] = 'True'


class TestProject(TestCase):
    def setUp(self):
        os.chdir(BASE_DIR)
        # if old stuff exists, remove it
        if os.path.exists(WOOEY_TEST_PROJECT_PATH):
            shutil.rmtree(WOOEY_TEST_PROJECT_PATH)

    def tearDown(self):
        os.chdir(BASE_DIR)
        if os.path.exists(WOOEY_TEST_PROJECT_PATH):
            shutil.rmtree(WOOEY_TEST_PROJECT_PATH)

    def test_bootstrap(self):
        from wooey.backend import command_line
        sys.argv = [WOOEY_SCRIPT_PATH, '-p', WOOEY_TEST_PROJECT_NAME]
        ret = command_line.bootstrap(env=env, cwd=BASE_DIR)
        self.assertIsNone(ret)
        # test our script is executable from the command line, it will fail with return code of 1 since
        # the project already exists
        proc = subprocess.Popen([PYTHON_INTERPRETTER, WOOEY_SCRIPT_PATH, '-p', WOOEY_TEST_PROJECT_NAME])
        stdout, stderr  = proc.communicate()
        self.assertEqual(proc.returncode, 1, stderr)
