from .djangui_settings import *

# This file is where the user can override and customize their installation of djangui

MEDIA_ROOT = os.path.join(BASE_DIR, 'user_uploads')
MEDIA_URL = '/uploads/'

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

## Celery related options
INSTALLED_APPS += ('djcelery',)
CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend'

## Additional djangui apps. These can be replaced with alternatives for further customization

INSTALLED_APPS += ('djguihome',)

# TODO: fix this name
POST_SCRIPT_URL = 'djangui_home'