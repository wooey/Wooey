from . import django_compat
if django_compat.DJANGO_VERSION >= django_compat.DJ17:
    default_app_config = 'djangui.apps.DjanguiConfig'
else:
    from .apps import DjanguiConfig
    DjanguiConfig().ready()