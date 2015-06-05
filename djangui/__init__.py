from . import version
import os
if version.DJANGO_VERSION >= version.DJ17:
    default_app_config = 'djangui.apps.DjanguiConfig'
else:
    if os.environ.get('TESTING') != 'True':
        from . import settings as djangui_settings
        # we need to call from within djangui_settings so the celery/etc vars are setup
        if not djangui_settings.settings.configured:
            djangui_settings.settings.configure()
        from .apps import DjanguiConfig
        DjanguiConfig().ready()