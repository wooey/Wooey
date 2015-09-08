from os import environ
from .wooey_settings import *
# This file is where the user can override and customize their installation of wooey

# Wooey Apps - add additional apps here after the initial install (remember to follow everything by a comma)

INSTALLED_APPS += (
)

# Whether to allow anonymous job submissions, set False to disallow 'guest' job submissions
WOOEY_ALLOW_ANONYMOUS = True

## Celery related options
INSTALLED_APPS += (
    'djcelery',
    'kombu.transport.django',
)

CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend'
BROKER_URL = 'django://'
CELERY_TRACK_STARTED = True
WOOEY_CELERY = True
CELERY_SEND_EVENTS = True
CELERY_IMPORTS = ('wooey.tasks')

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

## A better celery backend -- using RabbitMQ (these defaults are from two free rabbitmq Heroku providers)
# CELERY_RESULT_BACKEND = 'amqp'
# BROKER_URL = os.environ.get('AMQP_URL') or \
#              os.environ.get('RABBITMQ_BIGWIG_TX_URL') or \
#              os.environ.get('CLOUDAMQP_URL', 'amqp://guest:guest@localhost:5672/')
# BROKER_POOL_LIMIT = 1
# CELERYD_CONCURRENCY = 1
# CELERY_TASK_SERIALIZER = 'json'
# ACKS_LATE = True
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
