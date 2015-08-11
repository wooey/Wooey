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
        from .backend import utils
        try:
            utils.load_scripts()
        except:
            sys.stderr.write('Unable to load scripts:\n{}\n'.format(traceback.format_exc()))
        from . import signals
