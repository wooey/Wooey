import os

import six
from django.test import TestCase
from django.http.request import MultiValueDict
from django.core.files.uploadedfile import SimpleUploadedFile

from ..backend import utils
from ..forms import (
    factory,
    WooeyForm,
)
from ..forms import config as forms_config
from ..models import ScriptVersion, WooeyJob

from . import (
    config,
    factories,
    mixins,
    utils as test_utils,
)


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

    def test_groups_dont_duplicate(self):
        # fixes https://github.com/wooey/Wooey/issues/163
        # Update the translate script and make sure we do not duplicate form groups
        # Make a new script version
        old_translate_pk = self.translate_script.pk
        new_translate = self.translate_script
        new_translate.pk = None
        new_translate.save()
        old_translate = ScriptVersion.objects.get(pk=old_translate_pk)

        # Use a script that is slightly different but the same form groups
        script_path = test_utils.save_script_path(os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate2.py'))
        new_translate = utils.add_wooey_script(
            script_version=new_translate,
            script_path=script_path,
        )['script']

        # Assert we updated correctly
        self.assertEqual(old_translate.script.pk, new_translate.script.pk)
        self.assertEqual(old_translate.script_iteration, 1)
        self.assertEqual(new_translate.script_iteration, 2)

        # Make sure we still have the same number of groups after updating
        new_form = utils.get_form_groups(script_version=new_translate)
        old_form = utils.get_form_groups(script_version=old_translate)
        for new_parsers, old_parsers in zip(new_form['parsers'], old_form['parsers']):
            for new_subparser, old_subparser in zip(new_form['parsers'][new_parsers], old_form['parsers'][old_parsers]):
                self.assertEqual(new_subparser['group_name'], old_subparser['group_name'])

            self.assertEqual(len(new_parsers), len(old_parsers))

        self.assertEqual(len(new_form['parsers']), len(old_form['parsers']))

    def test_group_form(self):
        script_version = self.translate_script
        form = utils.get_form_groups(script_version=script_version)
        subparser = script_version.scriptparser_set.first()
        subparser_key = (subparser.pk, subparser.name)
        self.assertEqual(len(form['parsers'][subparser_key]), 2)
        # test we can hide parameters and groups
        from wooey.models import ScriptParameterGroup, ScriptParameter
        groups = ScriptParameterGroup.objects.filter(script_version=script_version)
        group = groups[1]
        group.hidden = True
        group.save()
        form = utils.get_form_groups(script_version=script_version)
        self.assertEqual(len(form['parsers'][subparser_key]), 1, 'Script Parameter group is hidden but shown')
        group.hidden = False
        group.save()
        form = utils.get_form_groups(script_version=script_version)
        self.assertEqual(len(form['parsers'][subparser_key]), 2, 'Script Parameter group is shown but hidden')
        param = ScriptParameter.objects.get(script_version=script_version, slug='out')
        param.hidden = True
        param.save()
        form = utils.get_form_groups(script_version=script_version)
        slug = test_utils.get_subparser_form_slug(script_version, 'out')
        self.assertNotIn(slug, form['parsers'][subparser_key][1]['form'].fields, 'Script Parameter is hidden but shown')
        param.hidden = False
        param.save()
        form = utils.get_form_groups(script_version=script_version)
        self.assertIn(slug, form['parsers'][subparser_key][1]['form'].fields, 'Script Parameter is shown but hidden')


    def test_multiplechoice_form(self):
        script_version = self.choice_script
        form = utils.get_master_form(script_version=script_version)
        # check our wrapper is in the form render
        form_str = str(form)
        self.assertTrue(forms_config.WOOEY_MULTI_WIDGET_ANCHOR in form_str)
        self.assertTrue(forms_config.WOOEY_MULTI_WIDGET_ATTR in form_str)

        qdict = {}
        for key,value in six.iteritems(config.SCRIPT_DATA['choices'].get('data')):
            try:
                form_slug = test_utils.get_subparser_form_slug(script_version, key)
                qdict[form_slug] = value
            except:
                qdict[key] = value
        qdict = self.get_mvdict(qdict)

        fdict = {}
        for key, value in six.iteritems(config.SCRIPT_DATA['choices'].get('files')):
            try:
                form_slug = test_utils.get_subparser_form_slug(script_version, key)
                fdict[form_slug] = value
            except:
                fdict[key] = value

        uploaded_files = {}
        storage = utils.get_storage(local=True)
        for file_key, files in fdict.items():
            uploaded_files[file_key] = []
            for file_location in files:
                file_name = os.path.split(file_location.name)[1]
                uploaded_files[file_key].append(SimpleUploadedFile(file_name, file_location.read()))

        utils.validate_form(
            form=form,
            data=qdict,
            files=uploaded_files
        )
        self.assertTrue(form.is_valid())
        # test we can create a job from this form
        # this is implemented to put data and files in the same dictionary, so update it
        form.cleaned_data.update(uploaded_files)
        job = utils.create_wooey_job(
            script_version_pk=script_version.pk,
            data=form.cleaned_data
        )
        # check the files are here
        file_param = test_utils.get_subparser_form_slug(script_version, 'multiple_file_choices')
        files = [i.value for i in job.get_parameters() if i.parameter.form_slug == file_param]
        self.assertEqual(len(files), len(uploaded_files.get(file_param)))

    def test_without_args_form(self):
        script_version = self.without_args
        form = utils.get_master_form(script_version=script_version)
        # check our wrapper is in the form render
        # in a normal POST request, the data will contain {'wooey_type': script_pk}. This will cause the is_bound
        # attribute of the form to be set. Otherwise, this test will always fail. It is OK to set this data
        # in the test, since it is how it will be recapitulated in the normal use case
        form_data = form.initial
        form_data.update(config.SCRIPT_DATA['without_args'].get('data'))
        utils.validate_form(form=form, data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        # test we can create a job from this form
        job = utils.create_wooey_job(script_version_pk=script_version.pk, data=form.cleaned_data)
        job.submit_to_celery()
        # get the job again
        job = WooeyJob.objects.get(pk=job.pk)
        self.assertEqual(job.status, WooeyJob.COMPLETED)

    def test_wooey_form(self):
        # Make sure wooey form exists and has everything we need in it
        script_version = self.without_args
        forms = utils.get_form_groups(script_version=self.without_args)
        wooey_form = forms['wooey_form']
        self.assertDictEqual(wooey_form.initial, {'wooey_type': script_version.pk})

    def test_multiple_file_field_initial_value(self):
        # Addresses https://github.com/wooey/Wooey/issues/248
        script_version = self.choice_script
        multiple_files_param = script_version.scriptparameter_set.get(script_param='multiple_file_choices')
        # Upload some fake files
        storage = utils.get_storage(local=False)
        storage.save('file1', SimpleUploadedFile('file1', b'abc'))
        file1_path = storage.path('file1')
        storage.save('file2', SimpleUploadedFile('file2', b'abc'))
        file2_path = storage.path('file2')
        form = utils.get_form_groups(script_version=script_version, initial_dict={
            multiple_files_param.form_slug: ['file1', 'file2']
        })
        # TODO: Make a function to ease this
        initial_files = [i.path for i in form['parsers'][(multiple_files_param.parser.pk, multiple_files_param.parser.name)][1]['form'].fields[multiple_files_param.form_slug].initial]
        self.assertIn(file1_path, initial_files)
        self.assertIn(file2_path, initial_files)

    def test_form_with_custom_widget(self):
        script_version = self.choice_script
        # Associate a custom widget with a field
        choice_param = script_version.scriptparameter_set.get(script_param='one_choice')
        widget = factories.WooeyWidgetFactory(
            widget_class='django.forms.TextInput',
            input_class='custom',
            input_properties='custom-property',
            input_attributes='attr1="custom1" attr2="custom2"'
        )
        choice_param.custom_widget = widget
        choice_param.save()
        form = utils.get_form_groups(script_version=script_version)

        from django.forms import TextInput
        field = form['parsers'][(choice_param.parser.pk, choice_param.parser.name)][1]['form'].fields[choice_param.form_slug]
        self.assertTrue(isinstance(field.widget, TextInput))
        self.assertEquals(
            field.widget.attrs,
            {
                'custom-property': True,
                'attr1': 'custom1',
                'attr2': 'custom2',
                'class': 'custom',
            }
        )
