from django.apps import AppConfig
from django.conf import settings


class DjanguiConfig(AppConfig):
    name = 'djangui'
    verbose_name = 'Djangui'

    def ready(self):
        from .backend import utils
        utils.load_scripts()
        settings.DJANGUI_HOME_URLS = getattr(settings, 'DJANGUI_HOME_URLS', 'djguihome.urls')