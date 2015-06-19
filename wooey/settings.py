__author__ = 'chris'
from django.conf import settings

def get(key, default):
    return getattr(settings, key, default)

WOOEY_FILE_DIR = get('WOOEY_FILE_DIR', 'wooey_files')
WOOEY_SCRIPT_DIR = get('WOOEY_SCRIPT_DIR', 'wooey_scripts')
WOOEY_CELERY = get('WOOEY_CELERY', True)
WOOEY_CELERY_TASKS = get('WOOEY_CELERY_TASKS', 'wooey.tasks')
WOOEY_ALLOW_ANONYMOUS = get('WOOEY_ALLOW_ANONYMOUS', True)
WOOEY_AUTH = get('WOOEY_AUTH', True)
WOOEY_LOGIN_URL = get('WOOEY_LOGIN_URL', settings.LOGIN_URL)
WOOEY_REGISTER_URL = get('WOOEY_REGISTER_URL', '/accounts/register/')
WOOEY_SHOW_LOCKED_SCRIPTS = get('WOOEY_SHOW_LOCKED_SCRIPTS', True)
WOOEY_EPHEMERAL_FILES = get('WOOEY_EPHEMERAL_FILES', False)
