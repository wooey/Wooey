import shutil

from ..models import Script, WooeyFile, WooeyJob
from ..backend import utils


class FileCleanupMixin(object):
    def tearDown(self):
        for i in WooeyFile.objects.all():
            utils.get_storage().delete(i.filepath.path)
        # delete job dirs
        local_storage = utils.get_storage(local=True)
        for i in WooeyJob.objects.all():
            shutil.rmtree(local_storage.path(i.get_output_path()))
        super(FileCleanupMixin, self).tearDown()


class ScriptFactoryMixin(object):
    def tearDown(self):
        for i in Script.objects.all():
            path = i.script_path.path
            utils.get_storage().delete(path)
            path += 'c' # handle pyc junk
            utils.get_storage().delete(path)
        super(ScriptFactoryMixin, self).tearDown()
