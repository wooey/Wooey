from __future__ import absolute_import
__author__ = 'chris'
import copy
import json
import six
from collections import OrderedDict

from django import forms

from .scripts import DjanguiForm
from ..backend import utils
from ..models import ScriptParameter


class DjanguiFormFactory(object):
    djangui_forms = {}

    @staticmethod
    def get_field(param, initial=None):
        field = param.form_field
        choices = json.loads(param.choices)
        field_kwargs = {'label': param.script_param.title(),
                        'required': param.required,
                        'help_text': param.param_help,
                        }
        if choices:
            field = 'ChoiceField'
            base_choices = [(None, '----')] if not param.required else []
            field_kwargs['choices'] = base_choices+[(str(i), str(i).title()) for i in choices]
        if field == 'FileField':
            if param.is_output:
                field = 'CharField'
                initial = None
            else:
                if initial is not None:
                    initial = utils.get_storage_object(initial) if not hasattr(initial, 'path') else initial
                    field_kwargs['widget'] = forms.ClearableFileInput()
        if initial is not None:
            field_kwargs['initial'] = initial
        field = getattr(forms, field)
        return field(**field_kwargs)

    def get_group_forms(self, model=None, pk=None, initial=None):
        pk = int(pk) if pk is not None else pk
        if pk is not None and pk in self.djangui_forms:
            if 'groups' in self.djangui_forms[pk]:
                return copy.deepcopy(self.djangui_forms[pk]['groups'])
        params = ScriptParameter.objects.filter(script=model).order_by('pk')
        # set a reference to the object type for POST methods to use
        script_id_field = forms.CharField(widget=forms.HiddenInput)
        group_map = {}
        for param in params:
            field = self.get_field(param, initial=initial.get(param.slug) if initial else None)
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
            form = DjanguiForm()
            if group_index == 0:
                form.fields['djangui_type'] = script_id_field
                form.fields['djangui_type'].initial = pk
            for field_pk, field in six.iteritems(group_info['fields']):
                form.fields[field_pk] = field
            d['groups'].append({'group_name': group_info['group'], 'form': str(form)})
        try:
            self.djangui_forms[pk]['groups'] = d
        except KeyError:
            self.djangui_forms[pk] = {'groups': d}
        # if the master form doesn't exist, create it while we have the model
        if 'master' not in self.djangui_forms[pk]:
            self.get_master_form(model=model, pk=pk)
        return d

    def get_master_form(self, model=None, pk=None):
        pk = int(pk) if pk is not None else pk
        if pk is not None and pk in self.djangui_forms:
            if 'master' in self.djangui_forms[pk]:
                return copy.deepcopy(self.djangui_forms[pk]['master'])
        master_form = DjanguiForm()
        params = ScriptParameter.objects.filter(script=model).order_by('pk')
        # set a reference to the object type for POST methods to use
        pk = model.pk
        script_id_field = forms.CharField(widget=forms.HiddenInput)
        master_form.fields['djangui_type'] = script_id_field
        master_form.fields['djangui_type'].initial = pk

        for param in params:
            field = self.get_field(param)
            master_form.fields[param.slug] = field
        try:
            self.djangui_forms[pk]['master'] = master_form
        except KeyError:
            self.djangui_forms[pk] = {'master': master_form}
        # create the group forms while we have the model
        if 'groups' not in self.djangui_forms[pk]:
            self.get_group_forms(model=model, pk=pk)
        return master_form

DJ_FORM_FACTORY = DjanguiFormFactory()