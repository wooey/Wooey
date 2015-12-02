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


class ScriptFactoryMixin(object):
    def tearDown(self):
        for i in ScriptVersion.objects.all():
            path = i.script_path.name
            # import pdb; pdb.set_trace();
            utils.get_storage().delete(path)
            if wooey_settings.WOOEY_EPHEMERAL_FILES:
                utils.get_storage(local=False).delete(path)
            path += 'c'  # handle pyc junk
            utils.get_storage().delete(path)
        super(ScriptFactoryMixin, self).tearDown()

    def setUp(self):
        self.translate_script = factories.generate_script(os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate.py'))
        self.choice_script = factories.generate_script(os.path.join(config.WOOEY_TEST_SCRIPTS, 'choices.py'))
        self.without_args = factories.generate_script(os.path.join(config.WOOEY_TEST_SCRIPTS, 'without_args.py'))
        super(ScriptFactoryMixin, self).setUp()

class FileMixin(object):
    def setUp(self):
        self.storage = utils.get_storage(local=not wooey_settings.WOOEY_EPHEMERAL_FILES)
        self.filename_func = lambda x: os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, x)
        super(FileMixin, self).setUp()

    def get_any_file(self):
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'command_order.py')
        return self.storage.save(self.filename_func('command_order.py'), open(script))