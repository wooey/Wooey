__author__ = 'chris'
import traceback
import sys

from wooey.version import DJANGO_VERSION, DJ110
if DJANGO_VERSION >= DJ110:
    from django.utils.deprecation import MiddlewareMixin
else:
    MiddlewareMixin = object

class ProcessExceptionMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if response.status_code != 200:
            try:
                sys.stderr.write('{}'.format(''.join(traceback.format_exc())))
            except AttributeError:
                pass
        return response