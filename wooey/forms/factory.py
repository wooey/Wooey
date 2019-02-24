from __future__ import absolute_import
__author__ = 'chris'
import copy
import json
import os
from collections import OrderedDict
from functools import partial

import six
from django import forms
from django.forms.utils import flatatt, format_html
from django.http.request import QueryDict
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe

from . import config
from .scripts import WooeyForm
from .. import version
from ..backend import utils
from ..models import ScriptVersion


def mutli_render(render_func, appender_data_dict=None):
    def render(name, value=None, attrs=None, renderer=None):
        if not isinstance(value, (list, tuple)):
            value = [value]
        values = value
        widget_renderer = partial(render_func, renderer=renderer) if renderer else partial(render_func)
        # The tag is a marker for our javascript to reshuffle the elements. This is because some widgets have complex rendering with multiple fields
        pieces = ['<{tag} {multi_attr}>{widget}</{tag}>'.format(tag='div', multi_attr=config.WOOEY_MULTI_WIDGET_ATTR,
                                                                widget=widget_renderer(name, value, attrs)) for value in values]

        # we add a final piece that is our button to click for adding. It's useful to have it here instead of the template so we don't
        # have to reverse-engineer who goes with what

        # build the attribute dict
        data_attrs = flatatt(appender_data_dict if appender_data_dict is not None else {})
        pieces.append(format_html('<a href="#{anchor}"{data}><span class="glyphicon glyphicon-plus"></span></a>', anchor=config.WOOEY_MULTI_WIDGET_ANCHOR
                                  , data=data_attrs))
        return mark_safe('\n'.join(pieces))
    return render


def multi_value_from_datadict(func):
    def value_from_datadict(data, files, name):
        return [func(QueryDict('{name}={value}'.format(name=name, value=i)), files, name) for i in data.getlist(name)]
    return value_from_datadict


def multi_value_clean(func):
    def clean(*args, **kwargs):
        args = list(args)
        values = args[0]
        ret = []
        for value in values:
            value_args = args
            value_args[0] = value
            ret.append(func(*value_args, **kwargs))
        return ret
    return clean


class WooeyFormFactory(object):
    wooey_forms = {}

    @staticmethod
    def get_field(param, initial=None):
        """
        Any extra field attributes for the widget for customization of Wooey at the field level
         can be added to the widget dictionary, widget_data_dict, or to the appender_data_dict, which
         is the little plus button. This is useful since there is only a single copy of the plus,
         whereas we can have multiple widgets. Thus, javascript attributes we want to add per parameter
         can be added to appender_data_dict, and attributes we want to add to the widget input itself
         can be added to the widget_data_dict.

        :return: a field class
        """
        form_field = param.form_field
        widget_data_dict = {}
        appender_data_dict = {}
        widget_init = {}
        WOOEY_CHOICE_LIMIT = 'data-wooey-choice-limit'
        choices = json.loads(param.choices)
        field_kwargs = {
            'label': param.script_param.replace('_', ' ').title(),
            'required': param.required,
            'help_text': param.param_help,
        }
        multiple_choices = param.multiple_choice
        choice_limit = param.max_choices
        if initial is None and param.default is not None:
            initial = param.default
        if choices:
            form_field = 'MultipleChoiceField' if multiple_choices else 'ChoiceField'
            base_choices = [(None, '----')] if not param.required and not multiple_choices else []
            field_kwargs['choices'] = base_choices+[(str(i), str(i).title()) for i in choices]

        custom_widget = param.custom_widget
        if custom_widget:
            if custom_widget.widget_class:
                widget_class = import_string(custom_widget.widget_class)
                field_kwargs['widget'] = widget_class
            widget_init['attrs'] = custom_widget.widget_attributes

        if form_field == 'FileField':
            if param.is_output:
                form_field = 'CharField'
                if initial:
                    if not isinstance(initial, (list, tuple)):
                        initial = [initial]
                    initial = [os.path.split(i.name)[1] for i in initial]
            elif initial is not None and list(filter(None, initial)):  # for python3, we need to evaluate the filter object
                if isinstance(initial, (list, tuple)):
                    _initial = []
                    for value in initial:
                        if not hasattr(value, 'path'):
                            with utils.get_storage_object(value, close=False) as so:
                                _initial.append(so)
                        else:
                            _initial.append(value)
                    initial = _initial
                else:
                    if not hasattr(initial, 'path'):
                        with utils.get_storage_object(initial, close=False) as so:
                            initial = so
                    else:
                        initial = initial
                if not field_kwargs.get('widget'):
                    field_kwargs['widget'] = forms.ClearableFileInput
        if not multiple_choices and isinstance(initial, list):
            initial = initial[0]
        field_kwargs['initial'] = initial
        field = getattr(forms, form_field)

        if 'widget' in field_kwargs:
            field_kwargs['widget'] = field_kwargs['widget'](**widget_init)

        field = field(**field_kwargs)

        if form_field != 'MultipleChoiceField' and multiple_choices:
            field.widget.render = mutli_render(field.widget.render, appender_data_dict=appender_data_dict)
            field.widget.value_from_datadict = multi_value_from_datadict(field.widget.value_from_datadict)
            field.clean = multi_value_clean(field.clean)
            if choice_limit > 0:
                appender_data_dict[WOOEY_CHOICE_LIMIT] = choice_limit
        elif multiple_choices and choice_limit>0:
            widget_data_dict[WOOEY_CHOICE_LIMIT] = choice_limit

        field.widget.attrs.update(widget_data_dict)
        return field

    def get_group_forms(self, script_version=None, pk=None, initial_dict=None, render_fn=None):
        pk = int(pk) if pk is not None else pk
        REQUIRED_GROUP = 'Required'
        if initial_dict is None:
            initial_dict = {}
        if pk is not None and pk in self.wooey_forms and initial_dict is None:
            if 'groups' in self.wooey_forms[pk]:
                if (version.PY_MINOR_VERSION == version.PY34 and version.PY_FULL_VERSION >= version.PY343) or \
                        (version.PY_MINOR_VERSION == version.PY33 and version.PY_FULL_VERSION >= version.PY336):
                    return copy.deepcopy(self.wooey_forms[pk]['groups'])
        params = [i for i in script_version.get_parameters() if not i.hidden]
        base_group_map = OrderedDict({
            REQUIRED_GROUP: {
                'group': REQUIRED_GROUP,
                'fields': OrderedDict(),
            }
        })
        parser_group_map = OrderedDict()

        for param in params:
            if param.parameter_group.hidden:
                continue
            parser = (param.parser_id, param.parser.name or '')
            group_map = parser_group_map.setdefault(parser, copy.deepcopy(base_group_map))
            initial_values = initial_dict.get(param.form_slug, None)
            field = self.get_field(param, initial=initial_values)
            field.name = param.form_slug
            group_name = REQUIRED_GROUP if param.required else param.parameter_group.group_name
            group = group_map.get(group_name, {
                'group': group_name,
                'fields': OrderedDict()
            })
            group['fields'][param.form_slug] = field
            group_map[group_name] = group

        # Add any missing parsers. This is needed if the script has no parameters
        added_subparsers = {i[1] for i in parser_group_map.keys()}
        for parser in script_version.scriptparser_set.order_by('pk'):
            if parser.name not in added_subparsers:
                parser_group_map[(parser.id, parser.name)] = copy.deepcopy(base_group_map)

        # If there are no required groups in a parser, remove them
        for parser, group_map in six.iteritems(parser_group_map):
            if not len(group_map[REQUIRED_GROUP]['fields']):
                del group_map[REQUIRED_GROUP]

        pk = script_version.pk
        form_initial = {
            'wooey_type': pk,
        }
        if initial_dict.get('wooey_parser') is not None:
            form_initial['wooey_parser'] = initial_dict['wooey_parser']
        wooey_form = WooeyForm(initial=form_initial)
        script_info = {
            'action': script_version.get_url(),
            'parsers': OrderedDict(),
            'wooey_form': wooey_form,
        }

        # create individual forms for each group and subparser
        for parser, group_map in six.iteritems(parser_group_map):
            parser_pk = parser[0]
            if wooey_form.fields['wooey_parser'].initial is None and parser_pk is not None:
                wooey_form.fields['wooey_parser'].initial = parser_pk
            parser_groups = script_info['parsers'].setdefault(parser, [])
            for group_index, group in enumerate(six.iteritems(group_map)):
                group_pk, group_info = group
                form = forms.Form()
                for form_slug, field in six.iteritems(group_info['fields']):
                    form.fields[form_slug] = field

                if render_fn:
                    form = render_fn(form)

                parser_groups.append({'group_name': group_info['group'], 'form': form})
        try:
            self.wooey_forms[pk]['groups'] = script_info
        except KeyError:
            self.wooey_forms[pk] = {'groups': script_info}

        # if the master form doesn't exist, create it while we have the model
        if 'master' not in self.wooey_forms[pk]:
            self.get_master_form(script_version=script_version, pk=pk)

        return script_info

    def get_master_form(self, script_version=None, pk=None):
        pk = int(pk) if pk is not None else pk
        if pk is not None and pk in self.wooey_forms:
            if 'master' in self.wooey_forms[pk]:
                if (version.PY_MINOR_VERSION == version.PY34 and version.PY_FULL_VERSION >= version.PY343) or \
                        (version.PY_MINOR_VERSION == version.PY33 and version.PY_FULL_VERSION >= version.PY336):
                    return copy.deepcopy(self.wooey_forms[pk]['master'])
        if script_version is None and pk is not None:
            script_version = ScriptVersion.objects.get(pk=pk)
        pk = script_version.pk

        master_form = WooeyForm(initial={'wooey_type': pk})

        params = script_version.get_parameters()
        for param in params:
            field = self.get_field(param)
            master_form.fields[param.form_slug] = field

        try:
            self.wooey_forms[pk]['master'] = master_form
        except KeyError:
            self.wooey_forms[pk] = {'master': master_form}

        # create the group forms while we have the model
        if 'groups' not in self.wooey_forms[pk]:
            self.get_group_forms(script_version=script_version, pk=pk)

        return master_form

    def reset_forms(self, script_version=None):
        if script_version is not None and script_version.pk in self.wooey_forms:
            del self.wooey_forms[script_version.pk]

DJ_FORM_FACTORY = WooeyFormFactory()
