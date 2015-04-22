#!/usr/bin/env python
import importlib
import os

from django.db import models


from djangui.db.models import DjanguiModel
from djangui.db import fields as djangui_fields

{% for model in models %}
class {{ model.class_name }}(DjanguiModel):
    # field related options
    djangui_options = {{ model.djangui_options }}
    djangui_output_options = {{ model.djangui_output_defaults }}
    djangui_groups = {{ model.djangui_groups }}
    djangui_output_path = os.path.join('user_output', '{{ model.class_name }}')
    optional_fields = {{ model.optional_fields }}
    djangui_model_description = """{{ model.djangui_model_description }}"""
    {% for field in model.fields %}{{ field }}
    {% endfor %}
    def get_absolute_url(self):
        return u'{0}/{1}'.format("{{ app_name }}", "{{ model.class_name }}")

{% endfor %}