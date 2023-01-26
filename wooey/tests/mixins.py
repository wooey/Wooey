import os
import shutil

from .. import settings as wooey_settings
from ..backend import utils
from ..models import ScriptVersion, WooeyFile, WooeyJob
from . import config, factories

# TODO: Track down where file handles are not being closed. This is not a problem on Linux/Mac, but is on Windows
# and likely reflects being careless somewhere as opposed to Windows being a PITA
try:
    WindowsError
except NameError:
    WindowsError = None


class FileCleanupMixin():
    def tearDown(self):
        for i in WooeyFile.objects.all():
            try:
                path = i.filepath.name
                utils.get_storage().delete(path)
                if wooey_settings.WOOEY_EPHEMERAL_FILES:
                    utils.get_storage(local=False).delete(path)
            except WindowsError:
                print(f'unable to delete {path}')
        # delete job dirs
        local_storage = utils.get_storage(local=True)
        for i in WooeyJob.objects.all():
            path = i.get_output_path()
            try:
                shutil.rmtree(local_storage.path(path))
            except WindowsError:
                print(f'unable to delete {path}')
        super().tearDown()


class ScriptTearDown():
    def tearDown(self):
        for i in ScriptVersion.objects.all():
            name = i.script_path.name
            utils.get_storage().delete(name)
            if wooey_settings.WOOEY_EPHEMERAL_FILES:
                try:
                    utils.get_storage(local=False).delete(name)
                except WindowsError:
                    print(f'unable to delete {name}')
            name += 'c'  # handle pyc junk
            try:
                utils.get_storage().delete(name)
            except WindowsError:
                print(f'unable to delete {name}')
        super().tearDown()


class ScriptFactoryMixin(ScriptTearDown):
    def setUp(self):
        self.translate_script = factories.generate_script(os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate.py'))
        self.choice_script = factories.generate_script(os.path.join(config.WOOEY_TEST_SCRIPTS, 'choices.py'))
        self.without_args = factories.generate_script(os.path.join(config.WOOEY_TEST_SCRIPTS, 'without_args.py'))
        self.subparser_script = factories.generate_script(os.path.join(config.WOOEY_TEST_SCRIPTS, 'subparser_script.py'))
        self.version1_script = factories.generate_script(
            os.path.join(config.WOOEY_TEST_SCRIPTS, 'versioned_script', 'v1.py'),
            script_name='version_test',
        )
        self.version2_script = factories.generate_script(
            os.path.join(config.WOOEY_TEST_SCRIPTS, 'versioned_script', 'v2.py'),
            script_name='version_test',
        )
        super().setUp()


class FileMixin():
    def setUp(self):
        self.storage = utils.get_storage(local=not wooey_settings.WOOEY_EPHEMERAL_FILES)
        self.filename_func = lambda x: os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, x)
        super().setUp()

    def get_any_file(self):
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'command_order.py')
        return self.storage.save(self.filename_func('command_order.py'), open(script))
