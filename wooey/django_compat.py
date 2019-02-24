from . version import DJANGO_VERSION, DJ18, DJ17, DJ16, DJ19, DJ110, DJ111, DJ20, DJ21
from django.conf import settings

try:
    settings.configure()
except RuntimeError:
    pass

if DJANGO_VERSION < DJ19:
    from django.template.base import TagHelperNode, parse_bits
else:
    from django.template.library import TagHelperNode, parse_bits

if DJANGO_VERSION >= DJ18:
    from django.template import Engine
    get_template_from_string = Engine.get_default().from_string
else:
    from django.template.loader import get_template_from_string

if DJANGO_VERSION >= DJ20:
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse
