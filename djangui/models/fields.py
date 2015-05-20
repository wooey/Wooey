from __future__ import absolute_import
__author__ = 'chris'
from django.db import models
from ..forms import fields as djangui_form_fields

class DjanguiOutputFileField(models.FileField):
    def formfield(self, **kwargs):
        # TODO: Make this from an app that is plugged in
        defaults = {'form_class': djangui_form_fields.DjanguiOutputFileField}
        defaults.update(kwargs)
        return super(DjanguiOutputFileField, self).formfield(**defaults)

class DjanguiUploadFileField(models.FileField):
    def formfield(self, **kwargs):
        # TODO: Make this from an app that is plugged in
        defaults = {'form_class': djangui_form_fields.DjanguiUploadFileField}
        defaults.update(kwargs)
        return super(DjanguiUploadFileField, self).formfield(**defaults)