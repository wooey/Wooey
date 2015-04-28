from django.apps import AppConfig
from django.conf import settings

from .backend import utils
from .models import Script


class DjanguiConfig(AppConfig):
    name = 'djangui'
    verbose_name = 'Djangui'

    def ready(self):
        utils.load_scripts()
        settings.DJANGUI_HOME_URLS = getattr(settings, 'DJANGUI_HOME_URLS', 'djguihome.urls')