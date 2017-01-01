from .django_settings import *
from wooey.version import DJANGO_VERSION, DJ17
from django.utils.translation import ugettext_lazy as _

INSTALLED_APPS += (
    # 'corsheaders',
    'wooey',
)

LANGUAGES = [
  ('de', _('German')),
  ('en', _('English')),
  ('fr', _('French')),
  ('ja', _('Japanese')),
  ('nl', _('Dutch')),
  ('zh-hans' if DJANGO_VERSION >= DJ17 else 'zh-cn', _('Simplified Chinese')),
]

NEW_MIDDLEWARE = []
for i in MIDDLEWARE_CLASSES:
    NEW_MIDDLEWARE.append(i)
    if i == 'django.contrib.sessions.middleware.SessionMiddleware':
        NEW_MIDDLEWARE.append('django.middleware.locale.LocaleMiddleware')

NEW_MIDDLEWARE.append('{{ project_name }}.middleware.ProcessExceptionMiddleware')
MIDDLEWARE_CLASSES = NEW_MIDDLEWARE

PROJECT_NAME = "{{ project_name }}"
WOOEY_CELERY_APP_NAME = 'wooey.celery'
WOOEY_CELERY_TASKS = 'wooey.tasks'
