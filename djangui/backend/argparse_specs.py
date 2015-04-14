import argparse
import sys
import json
import imp
import traceback

def is_upload(action):
    """Checks if this should be a user upload

    :param action:
    :return: True if this is a file we intend to upload from the user
    """
    # import pdb; pdb.set_trace();
    return 'r' in action.type._mode and (action.default is None or
                                         getattr(action.default, 'name') not in (sys.stderr.name, sys.stdout.name))

# input attributes we try to set:
# checked, name, type, value
# extra information we want to append:
# help,
# required,
# param (for executing the script and knowing if we need - or --),
# upload (boolean providing info on whether it's a file are we uploading or saving)
# choices (for selections)
# choice_limit (for multi selection)

CHOICE_LIMIT_MAP = {'?': '1', '+': '>=1', '*': '>=0'}

# We want to map to model fields as well as html input types we encounter in argparse
# keys are known variable types, as defined in __builtins__
# the model is a Django based model, which can be fitted in the future for other frameworks.
# The type is the HTML input type
# nullcheck is a function to determine if the default value should be checked  (for cases like default='' for strings)
# the attr_kwargs is a mapping of the action attributes to its related html input type. It is a dict
# of the form: {'name_for_html_input': {
# and either one or both of:
#  'action_name': 'attribute_name_on_action', 'callback': 'function_to_evaluate_action_and_return_value'} }

GLOBAL_ATTRS = ['model', 'type']

GLOBAL_ATTR_KWARGS = {
    'name': {'action_name': 'dest'},
    'value': {'action_name': 'default'},
    'required': {'action_name': 'required'},
    'help': {'action_name': 'help'},
    'param': {'callback': lambda x: x.option_strings[0]},
    'choices': {'callback': lambda x: x.choices},
    'choice_limit': {'callback': lambda x: CHOICE_LIMIT_MAP.get(x.nargs, x.nargs)}
    }

TYPE_FIELDS = {
    # Python Builtins
    bool: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
           'attr_kwargs': GLOBAL_ATTR_KWARGS},
    file: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
           'attr_kwargs': GLOBAL_ATTR_KWARGS},
    float: {'model': 'FloatField', 'type': 'text', 'html5-type': 'number', 'nullcheck': lambda x: x.default is None,
            'attr_kwargs': GLOBAL_ATTR_KWARGS},
    int: {'model': 'BigIntegerField', 'type': 'text', 'nullcheck': lambda x: x.default is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
    None: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
    str: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default == '' or x.default is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
    unicode: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default == '' or x.default is None,
              'attr_kwargs': GLOBAL_ATTR_KWARGS},

    # argparse Types
    argparse.FileType: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
                        'attr_kwargs': dict(GLOBAL_ATTR_KWARGS, **{
                            'value': None,
                            'required': {'callback': lambda x: x.required or x.default in (sys.stdout, sys.stdin)},
                            'upload': {'callback': is_upload}
                        })},
}

# There are cases where we can glean additional information about the form structure, e.g.
# a StoreAction with default=True can be different than a StoreTrueAction with default=False
ACTION_CLASS_TO_TYPE_FIELD = {
    argparse._StoreAction: dict(TYPE_FIELDS, **{

    }),
    argparse._StoreConstAction: dict(TYPE_FIELDS, **{

    }),
    argparse._StoreTrueAction: dict(TYPE_FIELDS, **{
        None: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
               'attr_kwargs': dict(GLOBAL_ATTR_KWARGS, **{
                    'checked': {'callback': lambda x: x.default},
                    'value': None,
                    })
               },
    }),
    argparse._StoreFalseAction: dict(TYPE_FIELDS, **{
        None: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
               'attr_kwargs': dict(GLOBAL_ATTR_KWARGS, **{
                    'checked': {'callback': lambda x: x.default},
                    'value': None,
                    })
               },
    })
}

class ArgParseNode(object):
    """
        This class takes an argument parser entry and assigns it to a Build spec
    """
    def __init__(self, action=None):
        fields = ACTION_CLASS_TO_TYPE_FIELD.get(type(action), TYPE_FIELDS)
        field_type = fields.get(action.type)
        if field_type is None:
            field_types = [i for i in fields.keys() if i is not None and issubclass(type(action.type), i)]
            if len(field_types) > 1:
                field_types = [i for i in fields.keys() if i is not None and isinstance(action.type, i)]
            if len(field_types) == 1:
                field_type = fields[field_types[0]]
        self.node_attrs = dict([(i, field_type[i]) for i in GLOBAL_ATTRS])
        null_check = field_type['nullcheck'](action)
        for attr, attr_dict in field_type['attr_kwargs'].iteritems():
            if attr_dict is None:
                continue
            if attr == 'value' and null_check:
                continue
            if 'action_name' in attr_dict:
                self.node_attrs[attr] = getattr(action, attr_dict['action_name'])
            elif 'callback' in attr_dict:
                self.node_attrs[attr] = attr_dict['callback'](action)

    def __str__(self):
        return json.dumps(self.node_attrs)


class ArgParseNodeBuilder(object):
    # TODO: Add groupings
    def __init__(self, script_path=None, script_name=None):
        try:
            print script_name, script_path
            module = imp.load_source(script_name, script_path)
            self.valid = True
        except:
            sys.stderr.write('Error while loading %s:\n'.format(script_name))
            sys.stderr.write('{0}\n'.format(traceback.format_exc()))
            self.valid = False
        else:
            parser = module.parser
            self.class_name = script_name
            self.script_path = script_path
            self.script_description = getattr(parser, 'description', None)
            self.script_groups = []
            self.nodes = []
            for action in parser._actions:
                # This is the help message of argparse
                if action.default == argparse.SUPPRESS:
                    continue
                node = ArgParseNode(action=action)
                self.nodes.append(node)

    def __str__(self):
        return json.dumps({'name': self.class_name, 'path': self.script_path,
                           'description': self.script_description, 'inputs': [i.node_attrs for i in self.nodes]})