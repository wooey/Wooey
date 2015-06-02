from __future__ import absolute_import
import argparse
import sys
import json
import imp
import traceback
import tempfile
import six
import copy
from collections import OrderedDict
from .ast import source_parser
from itertools import chain

def is_upload(action):
    """Checks if this should be a user upload

    :param action:
    :return: True if this is a file we intend to upload from the user
    """
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
    'param': {'callback': lambda x: x.option_strings[0] if x.option_strings else ''},
    'choices': {'callback': lambda x: x.choices},
    'choice_limit': {'callback': lambda x: CHOICE_LIMIT_MAP.get(x.nargs, x.nargs)}
    }

TYPE_FIELDS = {
    # Python Builtins
    bool: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
           'attr_kwargs': GLOBAL_ATTR_KWARGS},
    float: {'model': 'FloatField', 'type': 'text', 'html5-type': 'number', 'nullcheck': lambda x: x.default is None,
            'attr_kwargs': GLOBAL_ATTR_KWARGS},
    int: {'model': 'IntegerField', 'type': 'text', 'nullcheck': lambda x: x.default is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
    None: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},
    str: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default == '' or x.default is None,
          'attr_kwargs': GLOBAL_ATTR_KWARGS},

    # argparse Types
    argparse.FileType: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
                        'attr_kwargs': dict(GLOBAL_ATTR_KWARGS, **{
                            'value': None,
                            'required': {'callback': lambda x: x.required or x.default in (sys.stdout, sys.stdin)},
                            'upload': {'callback': is_upload}
                        })},
}
if six.PY2:
    TYPE_FIELDS.update({
        file: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
           'attr_kwargs': GLOBAL_ATTR_KWARGS},
        unicode: {'model': 'CharField', 'type': 'text', 'nullcheck': lambda x: x.default == '' or x.default is None,
              'attr_kwargs': GLOBAL_ATTR_KWARGS},
    })
elif six.PY3:
    import io
    TYPE_FIELDS.update({
        io.IOBase: {'model': 'FileField', 'type': 'file', 'nullcheck': lambda x: False,
           'attr_kwargs': GLOBAL_ATTR_KWARGS},
    })

def update_dict_copy(a, b):
    temp = copy.deepcopy(a)
    temp.update(b)
    return temp

# There are cases where we can glean additional information about the form structure, e.g.
# a StoreAction with default=True can be different than a StoreTrueAction with default=False
ACTION_CLASS_TO_TYPE_FIELD = {
    argparse._StoreAction: update_dict_copy(TYPE_FIELDS, {}),
    argparse._StoreConstAction: update_dict_copy(TYPE_FIELDS, {}),
    argparse._StoreTrueAction: update_dict_copy(TYPE_FIELDS, {
        None: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
               'attr_kwargs': update_dict_copy(GLOBAL_ATTR_KWARGS, {
                    'checked': {'callback': lambda x: x.default},
                    'value': None,
                    })
               },
    }),
    argparse._StoreFalseAction: update_dict_copy(TYPE_FIELDS, {
        None: {'model': 'BooleanField', 'type': 'checkbox', 'nullcheck': lambda x: x.default is None,
               'attr_kwargs': update_dict_copy(GLOBAL_ATTR_KWARGS, {
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
        for attr, attr_dict in six.iteritems(field_type['attr_kwargs']):
            if attr_dict is None:
                continue
            if attr == 'value' and null_check:
                continue
            if 'action_name' in attr_dict:
                self.node_attrs[attr] = getattr(action, attr_dict['action_name'])
            elif 'callback' in attr_dict:
                self.node_attrs[attr] = attr_dict['callback'](action)

    @property
    def name(self):
        return self.node_attrs.get('name')

    def __str__(self):
        return json.dumps(self.node_attrs)

    def to_django(self):
        """
         This is a debug function to see what equivalent django models are being generated
        """
        exclude = {'name', 'model'}
        field_module = 'models'
        django_kwargs = {}
        if self.node_attrs['model'] == 'CharField':
            django_kwargs['max_length'] = 255
        django_kwargs['blank'] = not self.node_attrs['required']
        try:
            django_kwargs['default'] = self.node_attrs['value']
        except KeyError:
            pass
        return u'{0} = {1}.{2}({3})'.format(self.node_attrs['name'], field_module, self.node_attrs['model'],
                                           ', '.join(['{0}={1}'.format(i,v) for i,v in six.iteritems(django_kwargs)]),)


class ArgParseNodeBuilder(object):
    def __init__(self, script_path=None, script_name=None):
        self.valid = True
        self.error = ''
        try:
            module = imp.load_source(script_name, script_path)
        except:
            sys.stderr.write('Error while loading {0}:\n'.format(script_path))
            self.error = '{0}\n'.format(traceback.format_exc())
            sys.stderr.write(self.error)
            self.valid = False
            return
        main_module = module.main.__globals__ if hasattr(module, 'main') else globals()
        parsers = [v for i, v in chain(six.iteritems(main_module), six.iteritems(vars(module)))
                   if issubclass(type(v), argparse.ArgumentParser)]
        if not parsers:
            f = tempfile.NamedTemporaryFile()
            ast_source = source_parser.parse_source_file(script_path)
            python_code = source_parser.convert_to_python(list(ast_source))
            f.write(six.b('\n'.join(python_code)))
            f.seek(0)
            module = imp.load_source(script_name, f.name)
            main_module = module.main.__globals__ if hasattr(module, 'main') else globals()
            parsers = [v for i, v in chain(six.iteritems(main_module), six.iteritems(vars(module)))
                   if issubclass(type(v), argparse.ArgumentParser)]
        if not parsers:
            sys.stderr.write('Unable to identify ArgParser for {0}:\n'.format(script_path))
            self.valid = False
            return
        parser = parsers[0]
        self.class_name = script_name
        self.script_path = script_path
        self.script_description = getattr(parser, 'description', None)
        self.script_groups = []
        self.nodes = OrderedDict()
        self.script_groups = []
        non_req = set([i.dest for i in parser._get_optional_actions()])
        self.optional_nodes = set([])
        self.containers = OrderedDict()
        for action in parser._actions:
            # This is the help message of argparse
            if action.default == argparse.SUPPRESS:
                continue
            node = ArgParseNode(action=action)
            container = action.container.title
            container_node = self.containers.get(container, None)
            if container_node is None:
                container_node = []
                self.containers[container] = container_node
            self.nodes[node.name] = node
            container_node.append(node.name)
            if action.dest in non_req:
                self.optional_nodes.add(node.name)

    def get_script_description(self):
        return {'name': self.class_name, 'path': self.script_path,
                'description': self.script_description,
                'inputs': [{'group': container_name, 'nodes': [self.nodes[node].node_attrs for node in nodes]}
                           for container_name, nodes in six.iteritems(self.containers)]}

    @property
    def json(self):
        return json.dumps(self.get_script_description())