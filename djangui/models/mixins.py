__author__ = 'chris'
class UpdateScriptsMixin(object):
    def save(self, **kwargs):
        super(UpdateScriptsMixin, self).save(**kwargs)
        from ..backend.utils import load_scripts
        load_scripts()