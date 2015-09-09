__author__ = 'chris'
import os
import sys
import tempfile

from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.conf import settings

from ...backend.utils import add_wooey_script, get_storage, default_storage
from ... import settings as wooey_settings

try:
    import urllib as request
    import urlparse
except ImportError:
    import urllib.request as request
    import urllib.parse as urlparse

import zipfile
import tarfile

ACCEPTED_ARCHIVE_EXTENSIONS = ['.zip', '.gz', '.gzip', '.tgz']


class Command(BaseCommand):
    help = 'Adds a script to Wooey'

    def add_arguments(self, parser):
        parser.add_argument('script', type=str, help='A script or folder of scripts to add to Wooey.')
        parser.add_argument('--group',
            dest='group',
            default='Scripts',
            help='The name of the group to create scripts under. Default: Wooey Scripts')

    def handle(self, *args, **options):
        script = options.get('script')
        if not script:
            if len(args):
                script = args[0]
            else:
                raise CommandError('You must provide a script path or directory containing scripts.')

        # Check for remote URL; zipfile, etc.
        # if it is download, extract to temporary folder + substitute scriptpath
        if urlparse.urlparse(script).scheme != "":
            # We have remote URL, download to temporary file with same suffix
            _, ext = os.path.splitext(script)
            tfile = tempfile.NamedTemporaryFile(suffix=ext)
            request.urlretrieve(script, tfile.name)
            script = tfile.name

        if any([script.endswith(ext) for ext in ACCEPTED_ARCHIVE_EXTENSIONS]):
            # We have an archive; create a temporary folder and extract there
            tfolder = tempfile.mkdtemp()
            if script.endswith('.zip'):
               with zipfile.ZipFile(script, "r") as zf:
                    zf.extractall(tfolder)

            else:
                # Must be gzip
                with tarfile.open(script, 'r:gz') as tf:
                    tf.extractall(tfolder)

            # Set the script path to the temporary folder and continue as normal
            script = tfolder

        if not os.path.exists(script):
            raise CommandError('{0} does not exist.'.format(script))
        group = options.get('group', 'Scripts')

        scripts = []
        if os.path.isdir(script):
            for dirpath, _, fnames in os.walk(script):
                scripts.extend([os.path.join(dirpath, fn) for fn in fnames])

        else:
            scripts.append(script) # Single script

        converted = 0
        for script in scripts:
            if script.endswith('.pyc') or '__init__' in script:
                continue
            if script.endswith('.py'):
                # Get the script name here (before storage changes it)
                script_name = os.path.splitext(os.path.basename(script))[0] # Get the base script name
                sys.stdout.write('Converting {}\n'.format(script))
                # copy the script to our storage
                with open(script, 'r') as f:
                    script = default_storage.save(os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, os.path.split(script)[1]), File(f))
                    if wooey_settings.WOOEY_EPHEMERAL_FILES:
                        # save it locally as well (the default_storage will default to the remote store)
                        local_storage = get_storage(local=True)
                        local_storage.save(os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, os.path.split(script)[1]), File(f))
                res = add_wooey_script(script_path=script, group=group, script_name=script_name)
                if res['valid']:
                    converted += 1
        sys.stdout.write('Converted {} scripts\n'.format(converted))
