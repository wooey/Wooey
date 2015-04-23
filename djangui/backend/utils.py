__author__ = 'chris'
from django.core.urlresolvers import reverse_lazy, reverse
from django.conf import settings
from django.utils.encoding import force_unicode
from django.utils.translation import gettext_lazy as _

def sanitize_name(name):
    return name.replace(' ', '_').replace('-', '_')

def sanitize_string(value):
    return value.replace('"', '\\"')

def get_djangui_model_json_url(app, model_name):
    return reverse_lazy('{0}_script_json'.format(app), kwargs={'script_name': model_name, 'app_name': app})

def is_djangui_model(model):
    from ..db.models import DjanguiModel
    return issubclass(model, DjanguiModel) and not isinstance(type(model), DjanguiModel)

def get_model_script_url(model, json=True):
    app = model._meta.app_label
    return reverse('{}_script_json'.format(app) if getattr(settings, 'DJANGUI_AJAX', False) and json else '{}_script'.format(app),
                               kwargs={'script_name': model._meta.object_name, 'app_name': app})

def get_modelform_dict(model, instance=None):
    from django.forms.models import modelform_factory
    required = set(model.get_required_fields())
    form = modelform_factory(model, fields=required, exclude=settings.DJANGUI_EXCLUDES)
    d = {'action': get_model_script_url(model), 'required': '', 'optional': ''}
    # clear the instance's output fields if we have one
    if instance is not None:
        for out_arg, out_to in instance.djangui_output_options.iteritems():
            setattr(instance, out_arg, None)
    d['required'] = str(form(instance=instance))
    form = modelform_factory(model, fields=model.get_optional_fields(), exclude=settings.DJANGUI_EXCLUDES)
    d['optional'] = str(form(instance=instance))
    d['groups'] = [{'group_name': force_unicode(_('Required')), 'form': d['required']}] if required-set(settings.DJANGUI_EXCLUDES) else []
    for group_name, group_fields in model.djangui_groups.iteritems():
        form = modelform_factory(model, fields=set(group_fields)-required, exclude=settings.DJANGUI_EXCLUDES)
        d['groups'].append({'group_name': group_name.title(), 'form': str(form(instance=instance))})
    return d