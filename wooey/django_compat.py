from . version import DJANGO_VERSION, DJ18, DJ17, DJ16, DJ19
from django.conf import settings

try:
    settings.configure()
except RuntimeError:
    pass

# JSON compatibility fixes
if DJANGO_VERSION < DJ17:
    import json
    from django.http import HttpResponse


    class JsonResponse(HttpResponse):
        """
            JSON response
            # from https://gist.github.com/philippeowagner/3179eb475fe1795d6515
        """

        def __init__(self, content, mimetype='application/json', status=None, content_type=None, **kwargs):
            super(JsonResponse, self).__init__(
                content=json.dumps(content),
                mimetype=mimetype,
                status=status,
                content_type=content_type,
            )


else:
    from django.http import JsonResponse

if DJANGO_VERSION < DJ19:
    from django.template.base import TagHelperNode, parse_bits
else:
    from django.template.library import TagHelperNode, parse_bits

if DJANGO_VERSION >= DJ18:
    from django.template import Engine
    get_template_from_string = Engine.get_default().from_string
else:
    from django.template.loader import get_template_from_string


if DJANGO_VERSION < DJ17:
    from django.forms.util import flatatt, format_html

else:
    from django.forms.utils import flatatt, format_html

def get_cache(cache):
    if DJANGO_VERSION < DJ17:
        from django.core.cache import get_cache
        return get_cache(cache)
    else:
        from django.core.cache import caches
        return caches[cache]
