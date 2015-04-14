__author__ = 'chris'
from django.db import models


class DjanguiModel(models.Model):
    djangui_job_name = models.CharField(max_length=255)
    djangui_job_description = models.TextField()

    class Meta:
        abstract = True

    def get_option_param(self, param):
        # returns the param argparse accepts (ie --p vs -p)
        return self.djangui_options.get(param)

    def get_output_default(self, param):
        return self.djangui_output_options.get(param)

    @classmethod
    def get_required_fields(cls):
        return [i.name for i in cls._meta.fields if i.name in cls.djangui_options and i.name not in cls.optional_fields or i.blank is False]

    @classmethod
    def get_optional_fields(cls):
        return cls.optional_fields.intersection([i.name for i in cls._meta.fields])-set(cls.get_required_fields())

    @classmethod
    def get_class_name(cls):
        return cls.__class__.__name__