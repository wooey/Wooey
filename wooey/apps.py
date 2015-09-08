import traceback
import sys

try:
    from django.apps import AppConfig
except ImportError:
    AppConfig = object


class WooeyConfig(AppConfig):
    name = 'wooey'
    verbose_name = 'Wooey'

    def ready(self):
        from . import signals
