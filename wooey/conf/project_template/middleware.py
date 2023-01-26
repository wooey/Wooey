__author__ = 'chris'
import sys
import traceback

from wooey.version import DJ110, DJANGO_VERSION

if DJANGO_VERSION >= DJ110:
    from django.utils.deprecation import MiddlewareMixin
else:
    MiddlewareMixin = object


class ProcessExceptionMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if response.status_code != 200:
            try:
                sys.stderr.write(f"{''.join(traceback.format_exc())}")
            except AttributeError:
                pass
        return response
