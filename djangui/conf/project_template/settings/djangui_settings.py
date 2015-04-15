from .django_settings import *

INSTALLED_APPS += (
    'djguicore',

    '{{ app_name }}',
)

PROJECT_NAME = "{{ project_name }}"
DJANGUI_CELERY_APP_NAME = '{0}.celery'.format(PROJECT_NAME)
DJANGUI_CELERY_TASKS = '{0}.tasks'.format(PROJECT_NAME)