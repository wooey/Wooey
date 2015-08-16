import shutil

from ..models import Script, WooeyFile, WooeyJob
from ..backend import utils
from .. import settings as wooey_settings


class FileCleanupMixin(object):
    def tearDown(self):
        for i in WooeyFile.objects.all():
            path = i.filepath.name
            utils.get_storage().delete(path)
            if wooey_settings.WOOEY_EPHEMERAL_FILES:
                utils.get_storage(local=False).delete(path)
        # delete job dirs
        local_storage = utils.get_storage(local=True)
        for i in WooeyJob.objects.all():
            shutil.rmtree(local_storage.path(i.get_output_path()))
        super(FileCleanupMixin, self).tearDown()


class ScriptFactoryMixin(object):
    def tearDown(self):
        for i in Script.objects.all():
            path = i.script_path.name
            # import pdb; pdb.set_trace();
            utils.get_storage().delete(path)
            if wooey_settings.WOOEY_EPHEMERAL_FILES:
                utils.get_storage(local=False).delete(path)
            path += 'c' # handle pyc junk
            utils.get_storage().delete(path)
        super(ScriptFactoryMixin, self).tearDown()
