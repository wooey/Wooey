import shutil
import os

from ..models import ScriptVersion, WooeyFile, WooeyJob
from ..backend import utils
from .. import settings as wooey_settings
from . import factories, config


# TODO: Track down where file handles are not being closed. This is not a problem on Linux/Mac, but is on Windows
# and likely reflects being careless somewhere as opposed to Windows being a PITA
try:
    WindowsError
except NameError:
    WindowsError = None


class FileCleanupMixin(object):
    def tearDown(self):
        for i in WooeyFile.objects.all():
            try:
                path = i.filepath.name
                utils.get_storage().delete(path)
                if wooey_settings.WOOEY_EPHEMERAL_FILES:
                    utils.get_storage(local=False).delete(path)
            except WindowsError:
                print('unable to delete {}'.format(path))
        # delete job dirs
        local_storage = utils.get_storage(local=True)
        for i in WooeyJob.objects.all():
            path = i.get_output_path()
            try:
                shutil.rmtree(local_storage.path(path))
            except WindowsError:
                    print('unable to delete {}'.format(path))
        super(FileCleanupMixin, self).tearDown()

class ScriptTearDown(object):
    def tearDown(self):
        for i in ScriptVersion.objects.all():
            name = i.script_path.name
            utils.get_storage().delete(name)
            if wooey_settings.WOOEY_EPHEMERAL_FILES:
                try:
                    utils.get_storage(local=False).delete(name)
                except WindowsError:
                    print('unable to delete {}'.format(name))
            name += 'c'  # handle pyc junk
            try:
                utils.get_storage().delete(name)
            except WindowsError:
                print('unable to delete {}'.format(name))
        super(ScriptTearDown, self).tearDown()

class ScriptFactoryMixin(ScriptTearDown, object):
    def setUp(self):
        self.translate_script = factories.generate_script(os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate.py'))
        self.choice_script = factories.generate_script(os.path.join(config.WOOEY_TEST_SCRIPTS, 'choices.py'))
        self.without_args = factories.generate_script(os.path.join(config.WOOEY_TEST_SCRIPTS, 'without_args.py'))
        self.version1_script = factories.generate_script(
            os.path.join(config.WOOEY_TEST_SCRIPTS, 'versioned_script', 'v1.py'),
            script_name='version_test',
        )
        self.version2_script = factories.generate_script(
            os.path.join(config.WOOEY_TEST_SCRIPTS, 'versioned_script', 'v2.py'),
            script_name='version_test',
        )
        super(ScriptFactoryMixin, self).setUp()

class FileMixin(object):
    def setUp(self):
        self.storage = utils.get_storage(local=not wooey_settings.WOOEY_EPHEMERAL_FILES)
        self.filename_func = lambda x: os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, x)
        super(FileMixin, self).setUp()

    def get_any_file(self):
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'command_order.py')
        return self.storage.save(self.filename_func('command_order.py'), open(script))