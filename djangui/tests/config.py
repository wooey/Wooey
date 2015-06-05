import os

BASE_DIR = os.path.split(__file__)[0]
DJANGUI_TEST_SCRIPTS = os.path.join(BASE_DIR, 'scripts')
DJANGUI_TEST_DATA = os.path.join(BASE_DIR, 'data')

SCRIPT_DATA = {
    'translate':
        {
            'data': {
                'djangui_type': '1',
                'job_name': 'abc',
                'sequence': 'ATATATATATA',
                'frame': '+3',
                'out': 'abc'
            }
        }
}