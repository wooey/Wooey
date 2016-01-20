from __future__ import unicode_literals
import os

from django.core.files import File
from django.conf import settings

BASE_DIR = os.path.split(__file__)[0]
WOOEY_TEST_SCRIPTS = os.path.join(BASE_DIR, 'scripts')
WOOEY_TEST_DATA = os.path.join(BASE_DIR, 'data')
WOOEY_TEST_REMOTE_STORAGE_DIR = 'remote_storage'
WOOEY_TEST_REMOTE_STORAGE_PATH = os.path.join(BASE_DIR, 'media', 'remote_storage')

# Because forms are input as lists by Django, all attributes here need to be
# list like as well. The MultiValueDict/QueryDict get method assumes a list and
# will take the first element in validation (so for a string like 'ATAT' it will
# provide 'A').
SCRIPT_DATA = {
    'translate':
        {
            'data': {
                'wooey_type': ['1'],
                'job_name': ['abc'],
                'sequence': ['ATATATATATA'],
                'frame': ['+3'],
                'out': ['abc']
            }
        },
    'choices':
        {
            'data': {
                'wooey_type': ['1'],
                'job_name': ['abc'],
                'two_choices': [1, 2],
            },
            'files': {
                'multiple_file_choices': [File(open(os.path.join(WOOEY_TEST_SCRIPTS, 'choices.py'), 'rb')),
                                          File(open(os.path.join(WOOEY_TEST_SCRIPTS, 'crop.py'), 'rb'))
                                          ]
            }
        },
    'without_args':
        {
            'data': {
                'job_name': ['abc'],
            }

        }
}
