__author__ = 'chris'
from django.conf import settings

def get(key, default):
    return getattr(settings, key, default)

DJANGUI_FILE_DIR = get('DJANGUI_FILE_DIR', 'djangui_files')
DJANGUI_CELERY = get('DJANGUI_CELERY', True)
DJANGUI_CELERY_TASKS = get('DJANGUI_CELERY_TASKS', 'djangui.tasks')
DJANGUI_ALLOW_ANONYMOUS = get('DJANGUI_ALLOW_ANONYMOUS', True)