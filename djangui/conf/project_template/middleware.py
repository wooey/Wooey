__author__ = 'chris'
import traceback
import sys

class ProcessExceptionMiddleware(object):
    def process_response(self, request, response):
        if response.status_code != 200:
            print '\n'.join(traceback.format_exception(*sys.exc_info()))
        return response