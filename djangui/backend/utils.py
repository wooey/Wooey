__author__ = 'chris'
from django.core.urlresolvers import reverse_lazy, reverse

def sanitize_name(name):
    return name.replace(' ', '_').replace('-','_')

def sanitize_string(value):
    return value.replace('"', '\\"')

def get_djangui_model_json_url(app, model_name):
    print app, model_name
    return reverse_lazy('{0}_script_json'.format(app), kwargs={'script_name': model_name})

def is_djangui_model(model):
    from ..db.models import DjanguiModel
    return issubclass(model, DjanguiModel) and not isinstance(type(model), DjanguiModel)