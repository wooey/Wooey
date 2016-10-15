from .django_settings import *
from wooey.version import DJANGO_VERSION, DJ110

INSTALLED_APPS += (
    # 'corsheaders',
    'wooey',
)

if DJANGO_VERSION < DJ110:
    MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
    MIDDLEWARE_CLASSES.append('{{ project_name }}.middleware.ProcessExceptionMiddleware')
else:
    # Using Django 1.10 +
    MIDDLEWARE = list(MIDDLEWARE)
    MIDDLEWARE.append('{{ project_name }}.middleware.ProcessExceptionMiddleware')


PROJECT_NAME = "{{ project_name }}"
WOOEY_CELERY_APP_NAME = 'wooey.celery'
WOOEY_CELERY_TASKS = 'wooey.tasks'
