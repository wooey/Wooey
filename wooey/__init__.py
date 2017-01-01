from . import version
import os
if version.DJANGO_VERSION >= version.DJ17:
    default_app_config = 'wooey.apps.WooeyConfig'
else:
    if os.environ.get('TESTING') != 'True' and os.environ.get('WOOEY_BOOTSTRAP') != 'True':
        from . import settings as wooey_settings
        # we need to call from within wooey_settings so the celery/etc vars are setup
        if not wooey_settings.settings.configured:
            wooey_settings.settings.configure()
        from .apps import WooeyConfig
        WooeyConfig().ready()
