from . version import DJANGO_VERSION, DJ111, DJ20, DJ21
from django.conf import settings

try:
    settings.configure()
except RuntimeError:
    pass

from django.template import Engine
get_template_from_string = Engine.get_default().from_string
