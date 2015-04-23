from .djangui_settings import *

# This file is where the user can override and customize their installation of djangui

# Djangui Apps - add additional apps here (remember to follow everything by a comma)
INSTALLED_APPS += (
    '{{ app_name }}',
)


## Additional djangui apps. These can be replaced with alternatives for further customization

INSTALLED_APPS += ('djguihome',)

# TODO: fix this name
POST_SCRIPT_URL = 'djangui_home'

DJANGUI_AJAX = True

DJANGUI_ALLOW_ANONYMOUS = True

CORS_ORIGIN_ALLOW_ALL = True


# Things you most likely do not need to change
MEDIA_ROOT = os.path.join(BASE_DIR, 'user_uploads')
MEDIA_URL = '/uploads/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

## Celery related options
INSTALLED_APPS += (
    'djcelery',
    'kombu.transport.django',
)
CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend'
BROKER_URL = 'django://'
CELERY_TRACK_STARTED = True
