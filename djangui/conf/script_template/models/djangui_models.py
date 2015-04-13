#!/usr/bin/env python
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.fields.files import FieldFile
from ..tasks import submit_script

from djangui.db.models import DjanguiModel
from djangui.db import fields as djangui_fields

{% for model in models %}
class {{ model.class_name }}(DjanguiModel):
    # field related options
    djangui_options = {{ model.djangui_options }}
    djangui_output_options = {{ model.djangui_output_defaults }}
    djangui_model_description = """{{ model.djangui_model_description }}"""
    djangui_celery_id = models.CharField(max_length=255, blank=True, null=True)
    djangui_celery_state = models.CharField(max_length=255, blank=True, null=True)
    {% for field in model.fields %}{{ field }}
    {% endfor %}
    def get_absolute_url(self):
        return u'{0}/{1}'.format("{{ app_name }}", "{{ model.class_name }}")
{% endfor %}