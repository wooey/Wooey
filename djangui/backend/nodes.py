from __future__ import absolute_import
__author__ = 'chris'
import argparse
import sys
import copy
import traceback
import os
from django.db.models import Model
from . import utils

# these values cannot be field names assigned by a script, for instances such as a script having a parameter
# 'save'
FORBIDDEN = set(dir(Model))

def filetype_filefield_default(kwargs, attr, default_kwargs, action, extra=None):
    model_name = default_kwargs['model_name']
    value = getattr(action, attr)
    # import pdb; pdb.set_trace();
    if value in (None, sys.stderr, sys.stdout, os.devnull):
        # For files we are saving (out script output), handle cases where they are
        # going to stdout/etc.
        if not is_upload(action):
            if not action.required:
                kwargs['blank'] = True
            if value == sys.stderr:
                kwargs['djangui_output_default'] = "stderr"
            elif value == sys.stdout:
                kwargs['djangui_output_default'] = "stdout"
            elif value == os.devnull or value is None:
                kwargs['djangui_output_default'] = "null"
        model_name = 'upload_to'
        value = ['user_upload' if is_upload(action) else 'user_output']
        value.append("" if extra is None else extra.get('class_name', ''))
        value = "'{0}'".format(os.path.join(*value))
    kwargs[model_name] = value

def filetype_filefield_blank(kwargs, attr, default_kwargs, action, extra=None):
    model_name = default_kwargs['model_name']
    default = action.default
    if is_upload(action) and default == sys.stdin:
        kwargs[model_name] = False

def str_charfield_default(kwargs, attr, default_kwargs, action, extra=None):
    model_name = default_kwargs['model_name']
    value = getattr(action, attr)
    if value is not None:
        kwargs[model_name] = '"{0}"'.format(value)

def charfield_choices(kwargs, attr, default_kwargs, action, extra=None):
    model_name = default_kwargs['model_name']
    value = getattr(action, attr)
    if value:
        kwargs[model_name] = [(i, i) for i in action.choices]

def str_charfield_choices(kwargs, attr, default_kwargs, action, extra=None):
    model_name = default_kwargs['model_name']
    value = getattr(action, attr)
    if value:
        kwargs[model_name] = [(i, i.title()) for i in action.choices]

def required_default(kwargs, attr, default_kwargs, action, extra=None):
    # this sets blank=False if required = True
    model_name = default_kwargs['model_name']
    value = getattr(action, attr)
    kwargs[model_name] = not value

UNIVERSAL_KWARGS = {
    'required': {'model_name': 'blank', 'callback': required_default},
    'default': {'model_name': 'default'},
    'choices': {'model_name': 'choices', 'callback': charfield_choices}
    }

TYPE_FIELDS = {
    file: {'field': 'FileField',
            'getattr_kwargs': {
                'default': {'model_name': 'default', 'callback': filetype_filefield_default},
                'required': {'model_name': 'blank', 'callback': filetype_filefield_blank}
            }},
    float: {'field': 'FloatField', 'kwargs': {}},
    None: {'field': 'CharField', 'kwargs': {'max_length': 255},
              'getattr_kwargs': {
                  'default': {'model_name': 'default', 'callback': str_charfield_default},
              },
          },
    unicode: {'field': 'CharField', 'kwargs': {'max_length': 255},
              'getattr_kwargs': {
                  'default': {'model_name': 'default', 'callback': str_charfield_default},
                  'choices': {'model_name': 'choices', 'callback': str_charfield_choices}
              },
          },
    int: {'field': 'CharField', 'kwargs': {'max_length': 255}},
    str: {'field': 'CharField', 'kwargs': {'max_length': 255},
              'getattr_kwargs': {
                  'default': {'model_name': 'default', 'callback': str_charfield_default},
                  'choices': {'model_name': 'choices', 'callback': str_charfield_choices}
              },
          },
    bool: {'field': 'BooleanField',},
    argparse.FileType: {'field': 'FileField',
                        'getattr_kwargs': {
                            'default': {'model_name': 'default', 'callback': filetype_filefield_default},
                            'required': {'model_name': 'blank', 'callback': filetype_filefield_blank}
                        }}
}

ACTION_CLASS_TO_MODEL_FIELD = {
    argparse._StoreAction: dict(TYPE_FIELDS, **{

    }),
    argparse._StoreConstAction: dict(TYPE_FIELDS, **{

    }),
    argparse._StoreTrueAction: dict(TYPE_FIELDS, **{
        None: {'field': 'BooleanField', 'kwargs': {'blank': True},},
    }),
    argparse._StoreFalseAction: dict(TYPE_FIELDS, **{
        None: {'field': 'BooleanField', 'kwargs': {'blank': True},},
    })
}

def is_upload(action):
    """Checks if this should be a user upload

    :param action:
    :return: True if this is a file we intend to upload from the user
    """
    # import pdb; pdb.set_trace();
    return 'r' in action.type._mode and (action.default is None or
                                         getattr(action.default, 'name') not in (sys.stderr.name, sys.stdout.name))

class ArgParseNode(object):
    """
        This class takes an argument parser entry and assigns it to a Django field
    """
    def __init__(self, action=None, model_field=None, class_name=''):
        try:
            model_field = copy.deepcopy(model_field)
            field = model_field['field']
            self.field_module = 'models'
            if field == 'FileField':
                self.field_module = 'djangui_fields'
                if is_upload(action):
                    field = 'DjanguiUploadFileField'
                else:
                    field = 'DjanguiOutputFileField'
            #         # it's somewhere we're saving output to
            #         model_field = copy.deepcopy(TYPE_FIELDS[str])
            #         field = model_field['field']
            #         del model_field['getattr_kwargs']
            self.kwargs = model_field.get('kwargs', {})
            self.kwargs.update({'help_text': '"{0}"'.format(utils.sanitize_string(action.help))})
            getattr_kwargs = copy.deepcopy(UNIVERSAL_KWARGS)
            getattr_kwargs.update(model_field.get('getattr_kwargs', {}))
            for attr, attr_dict in getattr_kwargs.iteritems():
                cb = attr_dict.get('callback', None)
                if cb is not None:
                    cb(self.kwargs, attr, attr_dict, action, extra={'class_name': class_name})
                else:
                    model_name = attr_dict['model_name']
                    value = getattr(action, attr)
                    self.kwargs[model_name] = value
            self.name = self.get_valid_name(action.dest)
            self.kwargs.update({'verbose_name': '"{}"'.format(action.dest)})
            self.field = field
            # if self.name == 'fasta':
            #     import pdb; pdb.set_trace();
        except:
            import traceback
            print traceback.format_exc()
            import pdb; pdb.set_trace();

    def get_valid_name(self, name):
        add = 0
        new_name = name
        while new_name in FORBIDDEN:
            add+=1
            new_name = '{0}_{1}'.format(name, add)
        return new_name

    def __unicode__(self):
        return u'{0} = {3}.{1}({2})'.format(self.name, self.field,
                                               ', '.join(['{0}={1}'.format(i,v) for i,v in self.kwargs.iteritems()]),
                                               self.field_module)

    def __str__(self):
        return str(self.__unicode__())


class ArgParseNodeBuilder(object):
    def __init__(self, script, parser, script_path):
        self.nodes = []
        self.djangui_options = {}
        # places to save files to
        self.djangui_output_defaults = {}
        self.class_name = script
        self.script_path = os.path.abspath(script_path)
        self.model_description = getattr(parser, 'description', None)
        self.script_groups = []
        non_req = set([i.dest for i in parser._get_optional_actions()])
        self.optional_nodes = set([])
        self.containers = {}
        for action in parser._actions:
            # This is the help message of argparse
            if action.default == argparse.SUPPRESS:
                continue
            container = action.container.title
            container_node = self.containers.get(container, None)
            if container_node is None:
                container_node = []
                self.containers[container] = container_node
            fields = ACTION_CLASS_TO_MODEL_FIELD.get(type(action), TYPE_FIELDS)
            field_type = fields.get(action.type)
            # print action
            if field_type is None:
                field_types = [i for i in fields.keys() if i is not None and issubclass(type(action.type), i)]
                if len(field_types) > 1:
                    field_types = [i for i in fields.keys() if i is not None and isinstance(action.type, i)]
                if len(field_types) == 1:
                    field_type = fields[field_types[0]]
                else:
                    sys.stderr.write('Error creating {0}\n. {1}'.format(action, traceback.format_exc()))
                    import pdb; pdb.set_trace();
                    continue
            node = ArgParseNode(action=action, model_field=field_type, class_name=self.class_name)
            self.nodes.append(node)
            container_node.append(node.name)
            self.djangui_options[node.name] = action.option_strings[0]
            if action.dest in non_req:
                self.optional_nodes.add(node.name)
            if node.field == 'DjanguiOutputFileField':
                try:
                    self.djangui_output_defaults[node.name] = node.kwargs.pop('djangui_output_default')
                except KeyError:
                    import pdb; pdb.set_trace();
            if node.field == 'DjanguiUploadFileField':
                pass

    def getModelDict(self):
        fields = [u'djangui_script_name = models.CharField(max_length=255, default="{0}")'.format(self.script_path)]
        fields += [str(node) for node in self.nodes]
        return {'class_name': self.class_name, 'fields': fields, 'djangui_options': self.djangui_options,
                'djangui_output_defaults': self.djangui_output_defaults,
                'djangui_model_description': self.model_description, 'optional_fields': self.optional_nodes,
                'djangui_groups': dict([(i, sorted(v)) for i,v in self.containers.iteritems()])}