# __author__ = 'chris'
# from unittest import TestCase
# import subprocess
# import os
# import shutil
#
# from djangui.backend import utils
#
# BASE_DIR = os.path.split(__file__)[0]
# DJANGUI_SCRIPT_PATH = '{}.py'.format(os.path.join(BASE_DIR, '..', '..', 'scripts', 'djanguify.py'))
# DJANGUI_TEST_SCRIPTS = os.path.join(BASE_DIR, 'scripts')
# DJANGUI_TEST_PROJECT_NAME = 'djangui_project'
# DJANGUI_TEST_PROJECT_PATH = os.path.join(BASE_DIR, DJANGUI_TEST_PROJECT_NAME)
# DJANGUI_TEST_PROJECT_MANAGE = '{}.py'.format(os.path.join(DJANGUI_TEST_PROJECT_PATH, 'manage'))
# PYTHON_INTERPRETTER = 'python'
# DJANGUI_PROCESS = None
# CELERY_PROCESS = None
#
# class TestProject(TestCase):
#     def setUp(self):
#         # start the project
#         # if old stuff exists, remove it
#         if os.path.exists(DJANGUI_TEST_PROJECT_PATH):
#             shutil.rmtree(DJANGUI_TEST_PROJECT_PATH)
#         global DJANGUI_PROCESS
#         proc = subprocess.Popen([PYTHON_INTERPRETTER, DJANGUI_SCRIPT_PATH, '-s', DJANGUI_TEST_SCRIPTS,
#                                 '-a', 'djangui_app', '-p', DJANGUI_TEST_PROJECT_NAME, '--no-server'], cwd=BASE_DIR)
#         proc.wait()
#         DJANGUI_PROCESS = subprocess.Popen([PYTHON_INTERPRETTER, DJANGUI_TEST_PROJECT_MANAGE, 'runserver'])
#         CELERY_PROCESS = subprocess.Popen([PYTHON_INTERPRETTER, DJANGUI_TEST_PROJECT_MANAGE, 'celery', 'worker'])
#
#     def tearDown(self):
#         global DJANGUI_PROCESS
#         DJANGUI_PROCESS.kill()
#         CELERY_PROCESS.kill()
#         shutil.rmtree(DJANGUI_TEST_PROJECT_PATH)
#
#     def test_simple(self):
#         assert(True) == True
#