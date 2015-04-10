#!/usr/bin/env python
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.fields.files import FieldFile
from ..tasks import submit_script
from . import fields as djangui_fields

class DjanguiModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super(DjanguiModel, self).save(*args, **kwargs)
        # In Celery, the filepaths are not always kept for some reason, so we process the fields here
        script_options = dict([(i.name, getattr(self, i.name)) for i in self._meta.fields])
        com = [script_options.pop('djangui_script_name')]
        script_options.pop('djangui_celery_id')
        script_options.pop('djangui_celery_state')
        for i, v in script_options.iteritems():
            param = self.get_option_param(i)
            if param is None:
                continue
            if isinstance(v, FieldFile):
                if not default_storage.exists(v.path):
                    # create the file we're writing to
                    getattr(self, i).save(v.path, ContentFile(''))
                com += [param, v.path]
            else:
                if str(v) == 'True':
                    com += [param]
                elif str(v) == 'False':
                    continue
                else:
                    com += [param, str(v)]
        results = submit_script.delay(com)
        self.djangui_celery_id = results.id
        self.djangui_celery_state = results.state
        super(DjanguiModel, self).save(*args, **kwargs)

    def get_option_param(self, param):
        # returns the param argparse accepts (ie --p vs -p)
        return self.djangui_options.get(param)

    def get_output_default(self, param):
        return self.djangui_output_options.get(param)

{% for model in models %}
class {{ model.class_name }}(DjanguiModel):
    # field related options
    djangui_options = {{ model.djangui_options }}
    djangui_output_options = {{ model.djangui_output_defaults }}
    djangui_celery_id = models.CharField(max_length=255, blank=True, null=True)
    djangui_celery_state = models.CharField(max_length=255, blank=True, null=True)
    {% for field in model.fields %}{{ field }}
    {% endfor %}
    def get_absolute_url(self):
        return u'{0}/{1}'.format("{{ app_name }}", "{{ model.class_name }}")
{% endfor %}