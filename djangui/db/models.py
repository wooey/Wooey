__author__ = 'chris'
from django.db import models
from django.conf import settings


class DjanguiModel(models.Model):
    # blank=True, null=True is to allow anonymous users to submit jobs
    # TODO: add a setting for allowing anonymous users
    djangui_user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    djangui_job_name = models.CharField(max_length=255)
    djangui_job_description = models.TextField()
    djangui_command = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def get_option_param(self, param):
        # returns the param argparse accepts (ie --p vs -p)
        return self.djangui_options.get(param)

    def get_output_default(self, param):
        try:
            return self._djangui_temp_output[param]
        except (KeyError, AttributeError) as e:
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