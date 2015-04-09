__author__ = 'chris'
import argparse
import sys
import copy
from . import utils

def filetype_filefield_default(kwargs, default_kwargs, action, extra=None):
    attr = default_kwargs['attr']
    model_name = default_kwargs['model_name']
    value = getattr(action, attr)
    if value is None:
        model_name = 'upload_to'
        value = "''" if extra is None else "'{0}/'".format(extra.get('class_name', ''))
    kwargs[model_name] = value

def str_charfield_default(kwargs, default_kwargs, action, extra=None):
    attr = default_kwargs['attr']
    model_name = default_kwargs['model_name']
    value = getattr(action, attr)
    kwargs[model_name] = '"{0}"'.format(value)

TYPE_FIELDS = {
    int: {'field': 'CharField', 'kwargs': {'max_length': 255},
          'getattr_kwargs': [{'model_name': 'default', 'attr': 'default'}]},
    str: {'field': 'CharField', 'kwargs': {'max_length': 255},
          'getattr_kwargs': [{'model_name': 'default', 'attr': 'default', 'callback': str_charfield_default}]},
    bool: {'field': 'BooleanField',
           'getattr_kwargs': [{'model_name': 'default', 'attr': 'default'}]},
    argparse.FileType: {'field': 'FileField',
                        'getattr_kwargs': [{'model_name': 'default', 'attr': 'default', 'callback': filetype_filefield_default},]}
}

ACTION_CLASS_TO_MODEL_FIELD = {
    argparse._StoreAction: dict(TYPE_FIELDS, **{

    }),
    argparse._StoreConstAction: dict(TYPE_FIELDS, **{

    }),
    argparse._StoreTrueAction: dict(TYPE_FIELDS, **{
        None: {'field': 'BooleanField', 'getattr_kwargs': [{'model_name': 'default', 'attr': 'default'},]},
    }),
    argparse._StoreFalseAction: dict(TYPE_FIELDS, **{
        None: {'field': 'BooleanField', 'getattr_kwargs': [{'model_name': 'default', 'attr': 'default'},]},
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
            if field == 'FileField':
                if is_upload(action):
                    pass
                else:
                    # it's somewhere we're saving output to
                    model_field = copy.deepcopy(TYPE_FIELDS[str])
                    field = model_field['field']
                    del model_field['getattr_kwargs']
            self.kwargs = model_field.get('kwargs', {})
            self.kwargs.update({'help_text': '"{0}"'.format(utils.sanitize_string(action.help))})
            for i in model_field.get('getattr_kwargs', []):
                cb = i.get('callback', None)
                if cb is not None:
                    cb(self.kwargs, i, action, extra={'class_name': class_name})
                else:
                    attr = i['attr']
                    model_name = i['model_name']
                    value = getattr(action, attr)
                    self.kwargs[model_name] = value
            self.name = action.dest
            self.field = field
        except:
            import traceback
            print traceback.format_exc()
            import pdb; pdb.set_trace();

    def __unicode__(self):
        return u'{0} = models.{1}({2})'.format(self.name, self.field,
                                               ', '.join(['{0}={1}'.format(i,v) for i,v in self.kwargs.iteritems()]))

    def __str__(self):
        return str(self.__unicode__())

class ArgParseNodeBuilder(object):
    def __init__(self, script, parser, script_path):

        self.nodes = []
        self.class_name = script
        self.script_path = script_path
        for action in parser._actions:
            # This is the help message of argparse
            if action.default == argparse.SUPPRESS:
                continue
            fields = ACTION_CLASS_TO_MODEL_FIELD.get(type(action), TYPE_FIELDS)
            field_type = fields.get(action.type)
            # print action
            if field_type is None:
                field_types = [i for i in fields.keys() if issubclass(type(action.type), i)]
                if len(field_types) > 1:
                    field_types = [i for i in fields.keys() if isinstance(action.type, i)]
                if len(field_types) == 1:
                    field_type = fields[field_types[0]]
                else:
                    print 'NOOO'
                    continue
            node = ArgParseNode(action=action, model_field=field_type, class_name=self.class_name)
            self.nodes.append(node)

    def getModelDict(self):
        fields = [u'djangui_script_name = models.CharField(max_length=255, default="{0}")'.format(self.script_path)]
        fields += [str(node) for node in self.nodes]
        return {'class_name': self.class_name, 'fields': fields}