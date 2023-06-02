__author__ = "chris"
import traceback
import sys


class ProcessExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code != 200:
            try:
                sys.stderr.write("{}".format("".join(traceback.format_exc())))
            except AttributeError:
                pass
        return response
