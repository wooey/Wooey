# This file is where the user can override and customize their installation of djangui

# Djangui Apps - add additional apps here after the initial install (remember to follow everything by a comma)

INSTALLED_APPS += (
    '{{ app_name }}',
)


## Apps which extend the core of Djangui. These can be replaced with alternatives for further customization

INSTALLED_APPS += (
    # the home screen, encompasses the entire front end of djangui
    'djguihome',
)

# TODO: fix this name
# The url to go to after a successful task submission -- it should be a url mapping for the home screen app.
POST_SCRIPT_URL = 'djangui_home'

# Whether to use Ajax (for things such as asynchronous task submission)
DJANGUI_AJAX = True

# Whether to allow anonymous job submissions, set False to disallow 'guest' job submissions
DJANGUI_ALLOW_ANONYMOUS = True

CORS_ORIGIN_ALLOW_ALL = True

## Celery related options
INSTALLED_APPS += (
    'djcelery',
    'kombu.transport.django',
)

CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend'
BROKER_URL = 'django://'
CELERY_TRACK_STARTED = True

## Setup database related things here. Here are some examples for non-development based settings





# Things you most likely do not need to change

# the directory for uploads (physical directory)
MEDIA_ROOT = os.path.join(BASE_DIR, 'user_uploads')
# the url mapping
MEDIA_URL = '/uploads/'

# the directory to store our webpage assets (images, javascript, etc.)
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# the url mapping
STATIC_URL = '/static/'
