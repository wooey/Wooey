import traceback
import sys

from django.apps import AppConfig
from django.conf import settings



class DjanguiConfig(AppConfig):
    name = 'djangui'
    verbose_name = 'Djangui'

    def ready(self):
        from .backend import utils
        try:
            utils.load_scripts()
        except:
            sys.stderr.write('Unable to load scripts:\n{}\n'.format(traceback.format_exc()))