#!/usr/bin/env python
from django.db import models

{% for model in models %}
class {{ model.class_name }}(models.Model):
    {% for field in model.fields %}{{ field }}
    {% endfor %}
    def get_absolute_url(self):
        return u'{0}/{1}'.format("{{ app_name }}", "{{ model.class_name }}")
{% endfor %}