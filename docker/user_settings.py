import os
from .wooey_settings import *

# Whether to allow anonymous job submissions, set False to disallow 'guest' job submissions
WOOEY_ALLOW_ANONYMOUS = True

## Celery related options
INSTALLED_APPS += (
    'django_celery_results',
)

WOOEY_CELERY = True
CELERY_RESULT_BACKEND = 'django-db'
CELERY_BROKER_URL = 'amqp://guest@rabbit'
CELERY_TRACK_STARTED = True
CELERY_SEND_EVENTS = True
CELERY_IMPORTS = ('wooey.tasks',)
CELERY_TASK_SERIALIZER = 'json'
CELERY_TASK_ACKS_LATE = True

# the directory for uploads (physical directory)
MEDIA_ROOT = os.path.join(BASE_DIR, 'user_uploads')
# the url mapping
MEDIA_URL = '/uploads/'

# the directory to store our webpage assets (images, javascript, etc.)
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# the url mapping
STATIC_URL = '/static/'
## Here is a setup example for production servers

## A postgres database -- for multiple users a sqlite based database is asking for trouble

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        # for production environments, these should be stored as environment variables
        # I also recommend the django-heroku-postgresify package for a super simple setup
        'NAME': os.environ.get('DATABASE_NAME', 'wooey'),
        'USER': os.environ.get('DATABASE_USER', 'wooey'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'wooey'),
        'HOST': os.environ.get('DATABASE_URL', 'localhost'),
        'PORT': os.environ.get('DATABASE_PORT', '5432')
    }
}

ALLOWED_HOSTS = (
    'localhost',
    '127.0.0.1',
)

AUTHENTICATION_BACKEND = 'django.contrib.auth.backends.ModelBackend'
