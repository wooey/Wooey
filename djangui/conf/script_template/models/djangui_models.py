#!/usr/bin/env python
from django.db import models
from django.db.models.fields.files import FieldFile
from ..tasks import submit_script

class DjanguiModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        super(DjanguiModel, self).save(*args, **kwargs)
        # In Celery, the filepaths are not always kept for some reason, so we process the fields here
        script_options = dict([(i.name, getattr(self, i.name)) for i in self._meta.fields])
        com = [script_options.pop('djangui_script_name')]
        for i,v in script_options.iteritems():
            param = self.get_option_param(i)
            if param is None:
                continue
            if isinstance(v, FieldFile):
                com += [param, v.path]
            else:
                if str(v) == 'True':
                    com += [param]
                elif str(v) == 'False':
                    continue
                else:
                    com += [param, str(v)]
        submit_script.delay(com)

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