from django.db.models.query_utils import DeferredAttribute
from django.forms.models import model_to_dict

from ..backend import utils


class UpdateScriptsMixin():
    pass


class WooeyPy2Mixin():
    def __unicode__(self):
        return unicode(self.__str__())
