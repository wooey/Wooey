#!/usr/bin/env python
import importlib

from django.db import models
from django.db.models.fields.files import FieldFile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings


from djangui.db.models import DjanguiModel
from djangui.db import fields as djangui_fields
from djangui.backend import utils

from djguicore.models import DjanguiJob

tasks = importlib.import_module(settings.DJANGUI_CELERY_TASKS)

def get_script_options(model):
    script_options = dict([(i.name, getattr(model, i.name)) for i in model._meta.fields])
    com = [script_options.pop('djangui_script_name')]
    script_options.pop('djangui_celery_id')
    script_options.pop('djangui_celery_state')
    for i, v in script_options.iteritems():
        param = model.get_option_param(i)
        if param is None:
            continue
        if isinstance(v, FieldFile):
            try:
                if not default_storage.exists(v.path):
                    # create the file we're writing to
                    getattr(model, i).save(v.path, ContentFile(''))
            except ValueError:
                getattr(model, i).save(model.get_output_default(i), ContentFile(''))
            com += [param, v.path]
        else:
            if str(v) == 'True':
                com += [param]
            elif str(v) == 'False':
                continue
            else:
                com += [param, str(v)]
    return com

class DjanguiAppModel(DjanguiModel):
    class Meta:
        abstract = True

    def submit_to_celery(self):
        script_options = get_script_options(self)
        results = tasks.submit_script.delay(script_options)
        self.djangui_celery_id = results.id
        self.djangui_celery_state = results.state
        self.save()
        job = DjanguiJob(djangui_user=self.djangui_user, content_object=self)
        job.save()

{% for model in models %}
class {{ model.class_name }}(DjanguiAppModel):
    # field related options
    djangui_options = {{ model.djangui_options }}
    djangui_output_options = {{ model.djangui_output_defaults }}
    optional_fields = {{ model.optional_fields }}
    djangui_model_description = """{{ model.djangui_model_description }}"""
    djangui_celery_id = models.CharField(max_length=255, blank=True, null=True)
    djangui_celery_state = models.CharField(max_length=255, blank=True, null=True)
    {% for field in model.fields %}{{ field }}
    {% endfor %}
    def get_absolute_url(self):
        return u'{0}/{1}'.format("{{ app_name }}", "{{ model.class_name }}")

{% endfor %}