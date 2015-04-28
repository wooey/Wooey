from .django_settings import *

INSTALLED_APPS += (
    # 'corsheaders',
    'djguicore',
)

# MIDDLEWARE_CLASSES = [[i] if i == 'django.middleware.common.CommonMiddleware' else ['corsheaders.middleware.CorsMiddleware',i] for i in MIDDLEWARE_CLASSES]
MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES.append('{{ project_name }}.middleware.ProcessExceptionMiddleware')

PROJECT_NAME = "{{ project_name }}"
DJANGUI_CELERY_APP_NAME = '{0}.celery'.format(PROJECT_NAME)
DJANGUI_CELERY_TASKS = '{0}.tasks'.format(PROJECT_NAME)

DJANGUI_EXCLUDES = ('djangui_script_name', 'djangui_celery_id', 'djangui_celery_state',
                    'djangui_job_name', 'djangui_job_description', 'djangui_user', 'djangui_command')