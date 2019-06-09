__author__ = 'chris'
import argparse
import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File

from ...backend.utils import add_wooey_script, default_storage, get_storage
from ... import settings as wooey_settings


class Command(BaseCommand):
    help = 'Adds a script to Wooey'

    def add_arguments(self, parser):
        parser.add_argument('script', type=str, help='A script or folder of scripts to add to Wooey.')
        parser.add_argument(
            '--group',
            dest='group',
            default=wooey_settings.WOOEY_DEFAULT_SCRIPT_GROUP,
            help='The name of the group to create scripts under. Default: Wooey Scripts'
        )
        parser.add_argument(
            '--name',
            dest='name',
            default=None,
            help='The name of the script. Default: None (uses the filename)'
        )
        parser.add_argument(
            '--update',
            dest='update',
            action='store_true',
            help=argparse.SUPPRESS
        )

    def handle(self, *args, **options):
        script = options.get('script')
        if options.get('update'):
            sys.stdout.write('Explicit script updates are no longer required and this flag is ignored.')
        if not script:
            if len(args):
                script = args[-1]
            else:
                raise CommandError('You must provide a script path or directory containing scripts.')
        if not os.path.exists(script):
            raise CommandError('{0} does not exist.'.format(script))
        group = options.get('group', 'Wooey Scripts')
        scripts = [os.path.join(script, i) for i in os.listdir(script)] if os.path.isdir(script) else [script]
        converted = 0
        for script in scripts:
            if script.endswith('.pyc') or '__init__' in script:
                continue
            if script.endswith('.py'):
                sys.stdout.write('Converting {}\n'.format(script))
                # copy the script to our storage
                base_name = options.get('name') or os.path.splitext(os.path.split(script)[1])[0]
                with open(script, 'r') as f:
                    script = default_storage.save(os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, os.path.split(script)[1]), File(f))
                    if wooey_settings.WOOEY_EPHEMERAL_FILES:
                        # save it locally as well (the default_storage will default to the remote store)
                        local_storage = get_storage(local=True)
                        local_storage.save(os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, os.path.split(script)[1]), File(f))
                add_kwargs = {
                    'script_path': script,
                    'group': group,
                    'script_name': base_name,
                }
                res = add_wooey_script(**add_kwargs)
                if res['valid']:
                    converted += 1
        sys.stdout.write('Converted {} scripts\n'.format(converted))
