__author__ = 'chris'
from django.conf import settings

def get(key, default):
    return getattr(settings, key, default)

DJANGUI_FILE_DIR = get('DJANGUI_FILE_DIR', 'djangui_files')
DJANGUI_SCRIPT_DIR = get('DJANGUI_SCRIPT_DIR', 'djangui_scripts')
DJANGUI_CELERY = get('DJANGUI_CELERY', True)
DJANGUI_CELERY_TASKS = get('DJANGUI_CELERY_TASKS', 'djangui.tasks')
DJANGUI_ALLOW_ANONYMOUS = get('DJANGUI_ALLOW_ANONYMOUS', True)
DJANGUI_AUTH = get('DJANGUI_AUTH', True)
DJANGUI_LOGIN_URL = get('DJANGUI_LOGIN_URL', settings.LOGIN_URL)
DJANGUI_REGISTER_URL = get('DJANGUI_REGISTER_URL', '/accounts/register/')
DJANGUI_SHOW_LOCKED_SCRIPTS = get('DJANGUI_SHOW_LOCKED_SCRIPTS', True)
DJANGUI_EPHEMERAL_FILES = get('DJANGUI_EPHEMERAL_FILES', False)