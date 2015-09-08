from . version import DJANGO_VERSION, DJ18, DJ17, DJ16
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

if DJANGO_VERSION >= DJ18:
    from django.template import Engine

else:
    from django.template import Template


    class Engine(object):
        @staticmethod
        def from_string(code):
            return Template(code)


# GenericForeignKey compatibility fixes
if DJANGO_VERSION < DJ18:
    from django.contrib.contenttypes.generic import GenericForeignKey

else:
    from django.contrib.contenttypes.fields import GenericForeignKey


if DJANGO_VERSION < DJ17:
    from django.forms.util import flatatt, format_html

else:
    from django.forms.utils import flatatt, format_html
