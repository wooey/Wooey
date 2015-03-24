"""
Converts argparse parser actions into json "Build Specs"
"""

from argparse import (
    _CountAction,
    _HelpAction,
    _StoreConstAction,
    _StoreFalseAction,
    _StoreTrueAction,
    ArgumentParser)
import argparse
import itertools
import sys

PY3 = sys.version_info.major > 2

VALID_WIDGETS = (
    'FileChooser',
    'MultiFileChooser',
    'FileSaver',
    'DirChooser',
    'DateChooser',
    'TextField',

    'SelectOne',
    'SelectMany',

    'Counter',
    'RadioGroup',
    'CheckBox',
    'RangeField',
)


class UnknownWidgetType(Exception):
    pass


def convert(parser):

    widget_dict = getattr(parser, 'widgets', {})

    mutually_exclusive_group = [
        mutex_action
        for group_actions in parser._mutually_exclusive_groups
        for mutex_action in group_actions._group_actions]

    base_actions = [(action, get_widget(action, widget_dict))
                    for action in parser._actions
                    if action not in mutually_exclusive_group]

    positional_args = get_required_and_positional_args(base_actions)

    return {
        'required': positional_args,
        'optional': list(itertools.chain(
            get_optionals_with_choices(base_actions),
            get_optionals_without_choices(base_actions),
            get_counter_style_optionals(base_actions),
            get_mutually_exclusive_optionals(mutually_exclusive_group),
            get_flag_style_optionals(base_actions)
        )),
        }


def get_widget(action, widgets):
    supplied_widget = widgets.get(action.dest, None)
    type_arg_widget = 'FileChooser' if type(action.type) == argparse.FileType else None
    return supplied_widget or type_arg_widget or None


def get_required_and_positional_args(actions):
    """
    Extracts positional or required args from the actions list
    In argparse, positionals are defined by either an empty option_strings
    or by the option_strings parameters being sans a leading hyphen
    """
    filtered_actions = [(action, widget)
                        for action, widget in actions
                        if not action.option_strings
                        or action.required == True]

    return [as_json(action, widget=widget or 'TextField')
            for action, widget in filtered_actions]


def get_optionals_with_choices(actions):
    """
    All optional arguments which are constrained
    to specific choices.
    """
    filtered_actions = [(action, widget)
                        for action, widget in actions
                        if action.choices
                        and action.required == False]

    jsons = []
    for action, widget in filtered_actions:
        if PY3 and isinstance(action.choices, range):
            widget = 'RangeField'
            action.choices = (action.choices.start, action.choices.stop, action.choices.step)
        elif action.nargs == "+":
            # FIXME: We can be smarter here; other possibilities for multiple selections
            widget = 'SelectMany'
        else:
            widget = 'SelectOne'

        jsons.append(as_json(action, widget=widget))

    return jsons

def get_optionals_without_choices(actions):
    """
    All actions which are:
      (a) Optional, but without        required choices
      (b) Not of a "boolean" type (storeTrue, etc..)
      (c) Of type _AppendAction

    e.g. anything which has an argument style like:
       >>>    -f myfilename.txt
    """
    boolean_actions = (
        _StoreConstAction, _StoreFalseAction,
        _StoreTrueAction
    )
    filtered_actions = [
        (action, widget)
        for action, widget in actions
        if action.option_strings
        and not action.choices
        and not isinstance(action, _CountAction)
        and not isinstance(action, _HelpAction)
        and type(action) not in boolean_actions
        and action.required == False]

    return [as_json(action, widget=widget or 'TextField')
            for action, widget in filtered_actions]


def get_flag_style_optionals(actions):
    """
    Gets all instances of "flag" type options.
    i.e. options which either store a const, or
    store boolean style options (e.g. StoreTrue).
    Types:
      _StoreTrueAction
      _StoreFalseAction
      _StoreConst
    """
    filtered_actions = [
        (action, widget)
        for action, widget in actions
        if isinstance(action, _StoreTrueAction)
        or isinstance(action, _StoreFalseAction)
        or isinstance(action, _StoreConstAction)
        and action.required == False]

    return [as_json(action, widget=widget or 'CheckBox')
            for action, widget in filtered_actions]


def get_counter_style_optionals(actions):
    """
    Returns all instances of type _CountAction
    """
    filtered_actions = [(action, widget)
                        for action, widget in actions
                        if isinstance(action, _CountAction)
                        and action.required == False]

    _json_options = [as_json(action, widget=widget or 'Counter')
                      for action, widget in filtered_actions]

    # Counter should show as Dropdowns, so pre-populare with numeric choices
    for opt in _json_options:
        opt['choices'] = range(10)
    return _json_options


def get_mutually_exclusive_optionals(mutex_group):
    if not mutex_group:
        return []

    options = [
        {
            'display_name': mutex_arg.dest,
            'help': mutex_arg.help,
            'nargs': mutex_arg.nargs or '',
            'commands': mutex_arg.option_strings,
            'choices': mutex_arg.choices,
            } for mutex_arg in mutex_group
    ]

    return [{
                'type': 'RadioGroup',
                'group_name': 'Choose Option',
                'data': options
            }]


def as_json(action, widget):
    if widget not in VALID_WIDGETS:
        raise UnknownWidgetType('Widget Type {0} is unrecognized'.format(widget))

    option_strings = action.option_strings

    try:
        typestr = action.type.__name__
    except AttributeError:
        typestr = type(action.type).__name__

    if type(action.default) in [type(None), int, str, bool, float, list, dict]:  # Other types that are JSONable?
        defaultval = action.default
    else:
        # This will work for classes or functions; might need to catch more here
        defaultval = action.default.__name__

    return {
        'name': action.dest,
        'type': typestr,

        'help': action.help,
        'nargs': action.nargs or '',
        'commands': action.option_strings,
        'choices': action.choices or [],
        'default': defaultval,

        'widget': widget,

        'required': action.required or False,
    }
