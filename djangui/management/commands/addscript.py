__author__ = 'chris'
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.core.files.storage import default_storage
from django.conf import settings

from ...backend.utils import add_djangui_script
from ... import settings as djangui_settings


class Command(BaseCommand):
    help = 'Adds a script to Djangui'

    def add_arguments(self, parser):
        parser.add_argument('script', type=str, help='A script or folder of scripts to add to Djangui.')
        parser.add_argument('--group',
            dest='group',
            default='Djangui Scripts',
            help='The name of the group to create scripts under. Default: Djangui Scripts')

    def handle(self, *args, **options):
        script = options.get('script')
        if not script:
            if len(args):
                 script = args[0]
            else:
                raise CommandError('You must provide a script path or directory containing scripts.')
        if not os.path.exists(script):
            raise CommandError('{0} does not exist.'.format(script))
        group = options.get('group', 'Djangui Scripts')
        scripts = [os.path.join(script, i) for i in os.listdir(script)] if os.path.isdir(script) else [script]
        converted = 0
        for script in scripts:
            if script.endswith('.pyc') or '__init__' in script:
                continue
            if script.endswith('.py'):
                sys.stdout.write('Converting {}\n'.format(script))
                # copy the script to our storage
                with open(script, 'r') as f:
                    script = default_storage.save(os.path.join(djangui_settings.DJANGUI_SCRIPT_DIR, os.path.split(script)[1]), File(f))
                added, error = add_djangui_script(script=os.path.abspath(os.path.join(settings.MEDIA_ROOT, script)), group=group)
                if added:
                    converted += 1
        sys.stdout.write('Converted {} scripts\n'.format(converted))