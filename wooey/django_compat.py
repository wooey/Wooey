from django.conf import settings

from .version import DJ20, DJ21, DJ111, DJANGO_VERSION

try:
    settings.configure()
except RuntimeError:
    pass

from django.template import Engine

get_template_from_string = Engine.get_default().from_string
