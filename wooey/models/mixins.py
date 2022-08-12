from django.db.models.query_utils import DeferredAttribute
from django.forms.models import model_to_dict

from ..backend import utils


class UpdateScriptsMixin(object):
    pass


class WooeyPy2Mixin(object):
    def __unicode__(self):
        return unicode(self.__str__())

