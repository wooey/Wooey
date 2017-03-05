from __future__ import absolute_import
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .mixins import WooeyPy2Mixin
from ..backend import utils

class WooeyWidget(WooeyPy2Mixin, models.Model):
    name = models.CharField(_('Widget Name'), max_length=50)
    input_attributes = models.TextField(
        verbose_name=_('Input Widget Extra Attributes'),
        help_text=_('Extra attributes to the input field. The extra attributes MUST be specified like key="value".'),
        null=True,
        blank=True,
    )
    input_class = models.CharField(
        max_length=255,
        verbose_name=_('Input Widget Class name(s)'),
        help_text=_('The class name(s) for the input field.'),
        null=True,
        blank=True,
    )
    input_properties = models.CharField(
        max_length=255,
        verbose_name=_('Input Widget Extra Properties'),
        help_text=_('Additional properties to append to the input field.'),
        null=True,
        blank=True,
    )


    @property
    def widget_attributes(self):
        attrs = {}

        properties = self.input_properties
        if properties is not None:
            for attr in properties.split(' '):
                attrs[attr] = True

        attributes = self.input_attributes
        if attributes is not None:
            for key, value in utils.tokenize_html_attributes(attributes):
                attrs[key] = value
        return attrs

    def __str__(self):
        return self.name