from .django_settings import *
from wooey.version import DJANGO_VERSION, DJ110
from django.utils.translation import ugettext_lazy as _

INSTALLED_APPS += (
    # 'corsheaders',
    'wooey',
)

if DJANGO_VERSION < DJ110:
    MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
    MIDDLEWARE_CLASSES.append('{{ project_name }}.middleware.ProcessExceptionMiddleware')
    MIDDLEWARE_OBJ = MIDDLEWARE_CLASSES
else:
    # Using Django 1.10 +
    MIDDLEWARE = list(MIDDLEWARE)
    MIDDLEWARE.append('{{ project_name }}.middleware.ProcessExceptionMiddleware')
    MIDDLEWARE_OBJ = MIDDLEWARE

LANGUAGES = [
    ('de', _('German')),
    ('en', _('English')),
    ('fr', _('French')),
    ('ja', _('Japanese')),
    ('nl', _('Dutch')),
    ('zh-hans', _('Simplified Chinese')),
    ('ko', _('Korean')),
]

NEW_MIDDLEWARE = []
for i in MIDDLEWARE_OBJ:
    NEW_MIDDLEWARE.append(i)
    if i == 'django.contrib.sessions.middleware.SessionMiddleware':
        NEW_MIDDLEWARE.append('django.middleware.locale.LocaleMiddleware')

NEW_MIDDLEWARE.append('{{ project_name }}.middleware.ProcessExceptionMiddleware')
if DJANGO_VERSION < DJ110:
    MIDDLEWARE_CLASSES = NEW_MIDDLEWARE
else:
    MIDDLEWARE = NEW_MIDDLEWARE

PROJECT_NAME = "{{ project_name }}"
WOOEY_CELERY_APP_NAME = 'wooey.celery'
WOOEY_CELERY_TASKS = 'wooey.tasks'
