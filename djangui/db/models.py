__author__ = 'chris'
from django.db import models
from django.db.models.fields.files import FieldFile
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

    @classmethod
    def get_required_fields(cls):
        return [i.name for i in cls._meta.fields if i.name in cls.djangui_options and (i.blank is True or i.default is None)]

    @classmethod
    def get_optional_fields(cls):
        required = set(cls.get_required_fields())
        return [i.name for i in cls._meta.fields if i.name in cls.djangui_options and i.name not in required]

    @classmethod
    def get_class_name(cls):
        return cls.__class__.__name__