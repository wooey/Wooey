from django.test import TestCase

from ..backend import utils
from ..forms import DjanguiForm

from . import factories
from . import config
from . import mixins


class FormTestCase(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):

    def test_master_form(self):
        script = factories.TranslateScriptFactory()
        form = utils.get_master_form(model=script)
        assert(isinstance(form, DjanguiForm) is True)
        utils.validate_form(form=form, data=config.SCRIPT_DATA['translate'].get('data'),
                            files=config.SCRIPT_DATA['translate'].get('files'))
        assert(form.is_valid() is True)

    def test_group_form(self):
        script = factories.TranslateScriptFactory()
        form = utils.get_form_groups(model=script)
        self.assertEqual(len(form['groups']), 1)