__author__ = 'chris'
import traceback
import sys


class ProcessExceptionMiddleware(object):
    def process_response(self, request, response):
        if response.status_code != 200:
            try:
                sys.stderr.write('{}'.format(''.join(traceback.format_exc())))
            except AttributeError:
                pass
        return response
