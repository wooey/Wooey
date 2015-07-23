from __future__ import absolute_import
__author__ = 'chris'
import copy
import json
import six
from collections import OrderedDict

from django import forms

from .scripts import WooeyForm
from ..backend import utils
from ..models import ScriptParameter

def mutli_render(render_func, field=None):
    def render(name, values, attrs=None):
        if not isinstance(values, (list, tuple)):
            values = [values]
        # The tag is a marker for our javascript to reshuffle the elements. This is because some widgets have complex rendering with multiple fields
        return '\n'.join(['<{tag} data-wooey-multiple>{widget}</{tag}>'.format(tag='div', widget=render_func(name, value, attrs)) for value in values])
    return render


class WooeyFormFactory(object):
    wooey_forms = {}

    @staticmethod
    def get_field(param, initial=None):
        """
        Any extra field attributes for the widget for customization of Wooey at the field level
         can be added to the widget dictionary, widget_data_dict

        :return: a field class
        """
        form_field = param.form_field
        choices = json.loads(param.choices)
        field_kwargs = {'label': param.script_param.title(),
                        'required': param.required,
                        'help_text': param.param_help,
                        }
        multiple_choices = param.multiple_choice
        if choices:
            form_field = 'MultipleChoiceField' if multiple_choices else 'ChoiceField'
            base_choices = [(None, '----')] if not param.required and not multiple_choices else []
            field_kwargs['choices'] = base_choices+[(str(i), str(i).title()) for i in choices]
        if form_field == 'FileField':
            if param.is_output:
                form_field = 'CharField'
        if form_field == 'FieldField':
            if param.is_output:
                initial = None
            elif filter(None, initial):
                if isinstance(initial, (list, tuple)):
                    initial = [utils.get_storage_object(value) if not hasattr(value, 'path') else value for value in initial if value is not None]
                else:
                    initial = utils.get_storage_object(initial) if not hasattr(initial, 'path') else initial
                field_kwargs['widget'] = forms.ClearableFileInput()
        # if not isinstance(initial, (list, tuple)):
        field_kwargs['initial'] = initial
        field = getattr(forms, form_field)
        field = field(**field_kwargs)
        widget_data_dict = {}
        if form_field != 'MultipleChoiceField' and multiple_choices:
            field.widget.render = mutli_render(field.widget.render, field=field)
            field.widget.attrs.update(widget_data_dict)
        return field

    def get_group_forms(self, model=None, pk=None, initial_dict=None):
        pk = int(pk) if pk is not None else pk
        if initial_dict is None:
            initial_dict = {}
        if pk is not None and pk in self.wooey_forms:
            if 'groups' in self.wooey_forms[pk]:
                return copy.deepcopy(self.wooey_forms[pk]['groups'])
        params = ScriptParameter.objects.filter(script=model).order_by('pk')
        # set a reference to the object type for POST methods to use
        script_id_field = forms.CharField(widget=forms.HiddenInput)
        group_map = {}
        for param in params:
            initial_values = initial_dict.get(param.slug, None)
            field = self.get_field(param, initial=initial_values)
            field.name = param.slug
            group_id = -1 if param.required else param.parameter_group.pk
            group_name = 'Required' if param.required else param.parameter_group.group_name
            group = group_map.get(group_id, {
                'group': group_name,
                'fields': OrderedDict()
            })
            group['fields'][param.slug] = field
            group_map[group_id] = group
        # create individual forms for each group
        group_map = OrderedDict([(i, group_map[i]) for i in sorted(group_map.keys())])
        d = {'action': model.get_url()}
        d['groups'] = []
        pk = model.pk
        for group_index, group in enumerate(six.iteritems(group_map)):
            group_pk, group_info = group
            form = WooeyForm()
            if group_index == 0:
                form.fields['wooey_type'] = script_id_field
                form.fields['wooey_type'].initial = pk
            for field_pk, field in six.iteritems(group_info['fields']):
                form.fields[field_pk] = field
            d['groups'].append({'group_name': group_info['group'], 'form': str(form)})
        try:
            self.wooey_forms[pk]['groups'] = d
        except KeyError:
            self.wooey_forms[pk] = {'groups': d}
        # if the master form doesn't exist, create it while we have the model
        if 'master' not in self.wooey_forms[pk]:
            self.get_master_form(model=model, pk=pk)
        return d

    def get_master_form(self, model=None, pk=None):
        pk = int(pk) if pk is not None else pk
        if pk is not None and pk in self.wooey_forms:
            if 'master' in self.wooey_forms[pk]:
                return copy.deepcopy(self.wooey_forms[pk]['master'])
        master_form = WooeyForm()
        params = ScriptParameter.objects.filter(script=model).order_by('pk')
        # set a reference to the object type for POST methods to use
        pk = model.pk
        script_id_field = forms.CharField(widget=forms.HiddenInput)
        master_form.fields['wooey_type'] = script_id_field
        master_form.fields['wooey_type'].initial = pk

        for param in params:
            field = self.get_field(param)
            master_form.fields[param.slug] = field
        try:
            self.wooey_forms[pk]['master'] = master_form
        except KeyError:
            self.wooey_forms[pk] = {'master': master_form}
        # create the group forms while we have the model
        if 'groups' not in self.wooey_forms[pk]:
            self.get_group_forms(model=model, pk=pk)
        return master_form

DJ_FORM_FACTORY = WooeyFormFactory()
