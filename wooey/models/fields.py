from __future__ import absolute_import
__author__ = 'chris'
from django.db import models
from ..forms import fields as wooey_form_fields


class WooeyOutputFileField(models.FileField):
    def formfield(self, **kwargs):
        # TODO: Make this from an app that is plugged in
        defaults = {'form_class': wooey_form_fields.WooeyOutputFileField}
        defaults.update(kwargs)
        return super(WooeyOutputFileField, self).formfield(**defaults)


class WooeyUploadFileField(models.FileField):
    def formfield(self, **kwargs):
        # TODO: Make this from an app that is plugged in
        defaults = {'form_class': wooey_form_fields.WooeyUploadFileField}
        defaults.update(kwargs)
        return super(WooeyUploadFileField, self).formfield(**defaults)
