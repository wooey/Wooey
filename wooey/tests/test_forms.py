from django.test import TestCase
from django.http.request import MultiValueDict

from ..backend import utils
from ..forms import WooeyForm
from ..forms import config as forms_config

from . import factories
from . import config
from . import mixins


class FormTestCase(mixins.ScriptFactoryMixin, mixins.FileCleanupMixin, TestCase):

    @staticmethod
    def get_mvdict(data):
        return MultiValueDict(data)

    def test_master_form(self):
        script_version = self.translate_script
        form = utils.get_master_form(script_version=script_version)
        self.assertTrue(isinstance(form, WooeyForm))
        qdict = self.get_mvdict(config.SCRIPT_DATA['translate'].get('data'))
        utils.validate_form(form=form, data=qdict,
                            files=config.SCRIPT_DATA['translate'].get('files'))
        self.assertTrue(form.is_valid())

    def test_group_form(self):
        script_version = self.translate_script
        form = utils.get_form_groups(script_version=script_version)
        self.assertEqual(len(form['groups']), 1)

    def test_multiplechoice_form(self):
        script_version = self.choice_script
        form = utils.get_master_form(script_version=script_version)
        # check our wrapper is in the form render
        form_str = str(form)
        self.assertTrue(forms_config.WOOEY_MULTI_WIDGET_ANCHOR in form_str)
        self.assertTrue(forms_config.WOOEY_MULTI_WIDGET_ATTR in form_str)
        qdict = self.get_mvdict(config.SCRIPT_DATA['choices'].get('data'))
        fdict = config.SCRIPT_DATA['choices'].get('files')
        utils.validate_form(form=form, data=qdict,
                            files=fdict)
        self.assertTrue(form.is_valid())
        # test we can create a job from this form
        # this is implemented to put data and files in the same dictionary, so update it
        form.cleaned_data.update(fdict)
        job = utils.create_wooey_job(script_version_pk=script_version.pk, data=form.cleaned_data)
        # check the files are here
        file_param = 'multiple_file_choices'
        files = [i.value for i in job.get_parameters() if i.parameter.slug == file_param]
        self.assertEqual(len(files), len(fdict.get(file_param)))
