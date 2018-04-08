import errno
import os
from .wooey_settings import *
# This file is where the user can override and customize their installation of wooey

# Wooey Apps - add additional apps here after the initial install (remember to follow everything by a comma)

INSTALLED_APPS += (
)

# Whether to allow anonymous job submissions, set False to disallow 'guest' job submissions
WOOEY_ALLOW_ANONYMOUS = True

## Celery related options

INSTALLED_APPS += (
    'django_celery_results',
    'kombu.transport.filesystem',
)

# This stores the results of tasks. For larger sites, a database may become slow and other solutions
# such as redis should be considered.
CELERY_RESULT_BACKEND = 'django-db'

# This should absolutely be changed to a non-filesystem based broker for production deployments!
# http://docs.celeryproject.org/en/latest/getting-started/brokers/
CELERY_BROKER_URL = 'filesystem://'

# This function exists just to ensure the filesystem has the correct folders
def ensure_path(path):
    try:
        os.makedirs(path)
    except Exception as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    return path

broker_dir = ensure_path(os.path.join(BASE_DIR, '.broker'))
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "data_folder_in": ensure_path(os.path.join(broker_dir, "out")),
    "data_folder_out": ensure_path(os.path.join(broker_dir, "out")),
    "data_folder_processed": ensure_path(os.path.join(broker_dir, "processed")),
}


CELERY_TRACK_STARTED = True
WOOEY_CELERY = True
CELERY_SEND_EVENTS = True
CELERY_IMPORTS = ('wooey.tasks',)

# A cache interface. This provides realtime updates for scriots and should definitely be changed
# to use something like redis or memcached in production
WOOEY_REALTIME_CACHE = 'default'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'wooey_cache_table',
    }
}

# Things you most likely do not need to change

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

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         # for production environments, these should be stored as environment variables
#         # I also recommend the django-heroku-postgresify package for a super simple setup
#         'NAME': os.environ.get('DATABASE_NAME', 'wooey'),
#         'USER': os.environ.get('DATABASE_USER', 'wooey'),
#         'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'wooey'),
#         'HOST': os.environ.get('DATABASE_URL', 'localhost'),
#         'PORT': os.environ.get('DATABASE_PORT', '5432')
#     }
# }

## A better celery broker -- using RabbitMQ (these defaults are from two free rabbitmq Heroku providers)
# CELERY_BROKER_URL = os.environ.get('AMQP_URL') or \
#              os.environ.get('RABBITMQ_BIGWIG_TX_URL') or \
#              os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/')
# CELERY_BROKER_POOL_LIMIT = 1
# CELERYD_CONCURRENCY = 1
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_TASK_ACKS_LATE = True
#

## for production environments, django-storages abstracts away much of the difficulty of various storage engines.
## Here is an example for hosting static and user generated content with S3

# from boto.s3.connection import VHostCallingFormat
#
# INSTALLED_APPS += (
#     'storages',
#     'collectfast',
# )

## We have user authentication -- we need to use https (django-sslify)
## NOTE: This is MIDDLEWARE and not MIDDLEWARE_CLASSES in Django 1.10+!
# if not DEBUG:
#     MIDDLEWARE_CLASSES = ['sslify.middleware.SSLifyMiddleware']+list(MIDDLEWARE_CLASSES)
#     SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#
# ALLOWED_HOSTS = (
#     'localhost',
#     '127.0.0.1',
#     "wooey.herokuapp.com",# put your site here
# )
#
# AWS_CALLING_FORMAT = VHostCallingFormat
#
# AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID', '')
# AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY', '')
# AWS_STORAGE_BUCKET_NAME = environ.get('AWS_STORAGE_BUCKET_NAME', '')
# AWS_AUTO_CREATE_BUCKET = True
# AWS_QUERYSTRING_AUTH = False
# AWS_S3_SECURE_URLS = True
# AWS_FILE_OVERWRITE = False
# AWS_PRELOAD_METADATA = True
# AWS_S3_CUSTOM_DOMAIN = environ.get('AWS_S3_CUSTOM_DOMAIN', '')
#
# GZIP_CONTENT_TYPES = (
#     'text/css',
#     'application/javascript',
#     'application/x-javascript',
#     'text/javascript',
# )
#
# AWS_EXPIREY = 60 * 60 * 7
# AWS_HEADERS = {
#     'Cache-Control': 'max-age=%d, s-maxage=%d, must-revalidate' % (AWS_EXPIREY,
#         AWS_EXPIREY)
# }
#
# STATIC_URL = 'http://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
# MEDIA_URL = '/user-uploads/'
#
# STATICFILES_STORAGE = DEFAULT_FILE_STORAGE = 'wooey.wooeystorage.CachedS3BotoStorage'
# WOOEY_EPHEMERAL_FILES = True

AUTHENTICATION_BACKEND = 'django.contrib.auth.backends.ModelBackend'
