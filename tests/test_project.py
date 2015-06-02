__author__ = 'chris'
from unittest import TestCase
import subprocess
import os
import shutil

BASE_DIR = os.path.split(__file__)[0]
DJANGUI_SCRIPT_PATH = os.path.join(BASE_DIR, '..', 'scripts', 'djanguify.py')
DJANGUI_TEST_PROJECT_NAME = 'djangui_project'
DJANGUI_TEST_PROJECT_PATH = os.path.join(BASE_DIR, DJANGUI_TEST_PROJECT_NAME)
DJANGUI_TEST_PROJECT_MANAGE = os.path.join(DJANGUI_TEST_PROJECT_PATH, 'manage.py')
PYTHON_INTERPRETTER = 'python'

env = os.environ
env['DJANGO_SETTINGS_MODULE'] = '{}.settings'.format(DJANGUI_TEST_PROJECT_NAME)
env['TESTING'] = 'True'

class TestProject(TestCase):
    def setUp(self):
        # if old stuff exists, remove it
        if os.path.exists(DJANGUI_TEST_PROJECT_PATH):
            shutil.rmtree(DJANGUI_TEST_PROJECT_PATH)

    def tearDown(self):
        shutil.rmtree(DJANGUI_TEST_PROJECT_PATH)

    def test_bootstrap(self):
        proc = subprocess.Popen([PYTHON_INTERPRETTER, DJANGUI_SCRIPT_PATH, '-p', DJANGUI_TEST_PROJECT_NAME],
                                cwd=BASE_DIR, env=env, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        self.assertEqual(proc.returncode, 0, msg=stderr)