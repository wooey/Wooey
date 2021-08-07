from . version import DJANGO_VERSION, DJ111, DJ20, DJ21
from django.conf import settings

try:
    settings.configure()
except RuntimeError:
    pass

if DJANGO_VERSION < DJ19:
    from django.template.base import TagHelperNode, parse_bits
else:
    from django.template.library import TagHelperNode, parse_bits

from django.template import Engine
get_template_from_string = Engine.get_default().from_string
