__author__ = 'chris'
import os
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


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
WOOEY_DEFAULT_SCRIPT_GROUP = get('WOOEY_DEFAULT_SCRIPT_GROUP', _('Scripts'))
WOOEY_SITE_NAME = get('WOOEY_SITE_NAME', _('Wooey!'))
WOOEY_SITE_TAG = get('WOOEY_SITE_TAG', _('A web UI for Python scripts'))
