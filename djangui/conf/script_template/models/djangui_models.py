#!/usr/bin/env python
import importlib
import os
import errno

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
    cwd = ''
    for i, v in script_options.iteritems():
        param = model.get_option_param(i)
        if param is None:
            continue
        if isinstance(v, FieldFile):
            try:
                if not default_storage.exists(v.path):
                    # create the file we're writing to
                    # To handle zipping files, and access to files not explicitly referenced in the script,
                    # we make a directory for each job.
                    if not cwd:
                        cwd = os.path.join(model.djangui_output_path, str(DjanguiJob.objects.count()))
                    getattr(model, i).save(cwd, ContentFile(''))
            except ValueError:
                getattr(model, i).save(model.get_output_default(i), ContentFile(''))
            com += [param, v.path]
        else:
            if str(v) == 'True':
                com += [param]
            elif str(v) == 'False':
                continue
            else:
                if v:
                    com += [param, str(v)]
    return com, cwd

class DjanguiAppModel(DjanguiModel):
    class Meta:
        abstract = True

    def submit_to_celery(self, resubmit=False):
        script_options, cwd = get_script_options(self)
        if not cwd:
            folder = os.path.join(self.djangui_output_path, str(DjanguiJob.objects.count()))
        else:
            folder = cwd
        cwd = os.path.join(settings.MEDIA_ROOT, folder)
        abscwd = os.path.abspath(cwd)
        try:
            os.makedirs(abscwd)
        except OSError as exc:
            # directory already exists
            if exc.errno == errno.EEXIST and os.path.isdir(abscwd):
                pass
            else:
                raise
        results = tasks.submit_script.delay(script_options, djangui_cwd=abscwd)
        if resubmit:
            # this is a method(hack) to clone ourselves and create a new object
            self.pk = None
        self.djangui_save_path = folder
        self.djangui_celery_id = results.id
        self.djangui_celery_state = results.state
        self.djangui_command = ' '.join(script_options)
        self.save()
        job = DjanguiJob(djangui_celery_id=self.djangui_celery_id, djangui_user=self.djangui_user, content_object=self)
        job.save()
        return self

{% for model in models %}
class {{ model.class_name }}(DjanguiAppModel):
    # field related options
    djangui_options = {{ model.djangui_options }}
    djangui_output_options = {{ model.djangui_output_defaults }}
    djangui_groups = {{ model.djangui_groups }}
    djangui_output_path = os.path.join('user_output', '{{ model.class_name }}')
    optional_fields = {{ model.optional_fields }}
    djangui_model_description = """{{ model.djangui_model_description }}"""
    djangui_celery_id = models.CharField(max_length=255, blank=True, null=True)
    djangui_celery_state = models.CharField(max_length=255, blank=True, null=True)
    djangui_save_path = models.CharField(max_length=255, blank=True, null=True)
    {% for field in model.fields %}{{ field }}
    {% endfor %}
    def get_absolute_url(self):
        return u'{0}/{1}'.format("{{ app_name }}", "{{ model.class_name }}")

{% endfor %}