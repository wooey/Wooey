#!/usr/bin/env python
from django.db import models
from ..tasks import submit_script

class DjanguiModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super(DjanguiModel, self).save(*args, **kwargs)
        script_options = dict([(i.name, getattr(self, i.name)) for i in self._meta.fields])
        script_options['djangui_model'] = self
        submit_script(**script_options)

    def get_option_param(self, param):
        # returns the param argparse accepts (ie --p vs -p)
        return self.options.get(param)

{% for model in models %}
class {{ model.class_name }}(DjanguiModel):
    # field related options
    options = {{ model.options }}
    {% for field in model.fields %}{{ field }}
    {% endfor %}
    def get_absolute_url(self):
        return u'{0}/{1}'.format("{{ app_name }}", "{{ model.class_name }}")
{% endfor %}