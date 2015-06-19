__author__ = 'chris'
from unittest import TestCase
import subprocess
import os
import shutil

BASE_DIR = os.path.split(__file__)[0]
WOOEY_SCRIPT_PATH = os.path.join(BASE_DIR, '..', 'scripts', 'wooify.py')
WOOEY_TEST_PROJECT_NAME = 'wooey_project'
WOOEY_TEST_PROJECT_PATH = os.path.join(BASE_DIR, WOOEY_TEST_PROJECT_NAME)
WOOEY_TEST_PROJECT_MANAGE = os.path.join(WOOEY_TEST_PROJECT_PATH, 'manage.py')
PYTHON_INTERPRETTER = 'python'

env = os.environ
env['DJANGO_SETTINGS_MODULE'] = '{}.settings'.format(WOOEY_TEST_PROJECT_NAME)
env['TESTING'] = 'True'

class TestProject(TestCase):
    def setUp(self):
        # if old stuff exists, remove it
        if os.path.exists(WOOEY_TEST_PROJECT_PATH):
            shutil.rmtree(WOOEY_TEST_PROJECT_PATH)

    def tearDown(self):
        shutil.rmtree(WOOEY_TEST_PROJECT_PATH)

    def test_bootstrap(self):
        proc = subprocess.Popen([PYTHON_INTERPRETTER, WOOEY_SCRIPT_PATH, '-p', WOOEY_TEST_PROJECT_NAME],
                                cwd=BASE_DIR, env=env, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        self.assertEqual(proc.returncode, 0, msg=stderr)
